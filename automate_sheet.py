import os
import json
import time
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import shutil
from datetime import datetime

# Constants
TO_PROCESS_FOLDER = './toProcess/json/'
PROCESSED_FOLDER = './processed/json/'
SPREADSHEET_NAME = 'SPREADSHEET_NAME'
F_DB_SHEET = 'F DB'
O_DB_SHEET = 'O DB'
GAME_DB_SHEET = 'GAME DB'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

class GoogleSheetsClient:
    def __init__(self):
        self.client = self.authenticate_google_sheets()

    def authenticate_google_sheets(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return gspread.authorize(creds)

    def get_sheet(self, sheet_name):
        try:
            spreadsheet = self.client.open(SPREADSHEET_NAME)
            return spreadsheet.worksheet(sheet_name)
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{sheet_name}' not found.")
        return None

class GameDataProcessor:
    def __init__(self, client):
        self.client = client
        self.f_db_sheet = self.client.get_sheet(F_DB_SHEET)
        self.o_db_sheet = self.client.get_sheet(O_DB_SHEET)
        self.game_db_sheet = self.client.get_sheet(GAME_DB_SHEET)
        self.existing_hashes = self.game_db_sheet.col_values(41) if self.game_db_sheet else []
        self.next_game_id = self.get_next_game_id()

    def get_next_game_id(self):
        records = self.game_db_sheet.get_all_records() if self.game_db_sheet else []
        if not records:
            return 1
        last_game_id = max(int(record['GameID']) for record in records if str(record['GameID']).isdigit())
        return last_game_id + 1

    def convert_to_number(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def exponential_backoff(self, func, *args, max_retries=5, **kwargs):
        delay = 8
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 429:
                    print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    raise
        raise Exception("Max retries exceeded")

    def log_data_to_sheet(self, sheet, data):
        data = [self.convert_to_number(item) for item in data]
        print(f"Appending data to sheet {sheet.title}: {data}")
        self.exponential_backoff(sheet.append_row, data)

    def process_json_file(self, file_path):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            hash_value = data.get('hash')

            if hash_value in self.existing_hashes:
                print(f"Hash {hash_value} already exists.")
                return

            team1_name = data.get('team1_name', 'team1')
            team2_name = data.get('team2_name', 'team2')

            print(f"\nTeam 1: {team1_name}")
            for player in data['players']:
                if player.get('team') == 'team1':
                    print(f"  Player {player.get('player_number')}: {player.get('name').lower()}")

            print(f"\nTeam 2: {team2_name}")
            for player in data['players']:
                if player.get('team') == 'team2':
                    print(f"  Player {player.get('player_number')}: {player.get('name').lower()}")

            friendly_team = input(f"\nWhich team is friendly? (1 for '{team1_name}', 2 for '{team2_name}'): ").strip()
            is_team1_friendly = friendly_team == '1'
            is_team2_friendly = friendly_team == '2'

            team1_quarters = data.get('teams', {}).get('team1_quarters', {})
            team2_quarters = data.get('teams', {}).get('team2_quarters', {})
            team1_total = sum(int(team1_quarters.get(q, 0)) for q in ['quarter_1', 'quarter_2', 'quarter_3', 'quarter_4'])
            team2_total = sum(int(team2_quarters.get(q, 0)) for q in ['quarter_1', 'quarter_2', 'quarter_3', 'quarter_4'])

            team1_result, team2_result = ('W', 'L') if team1_total > team2_total else ('L', 'W')

            team1_stats, team2_stats = self.initialize_team_stats(), self.initialize_team_stats()

            # Create a dictionary to store players by team and position
            players_by_team_and_position = {'team1': {}, 'team2': {}}
            for player in data['players']:
                team = player.get('team')
                position = player.get('position')
                if team not in players_by_team_and_position:
                    players_by_team_and_position[team] = {}
                if position not in players_by_team_and_position[team]:
                    players_by_team_and_position[team][position] = []
                players_by_team_and_position[team][position].append(player)

            for player in data['players']:
                player_team = player.get('team')
                result = team1_result if player_team == 'team1' else team2_result
                team_stats = team1_stats if player_team == 'team1' else team2_stats

                for stat in team_stats.keys():
                    team_stats[stat] += int(player.get(stat, 0))

                PM2, PA2 = self.calculate_player_stats(player)
                if player_team == 'team1':
                    team1_stats['2PM'] += PM2
                    team1_stats['2PA'] += PA2
                else:
                    team2_stats['2PM'] += PM2
                    team2_stats['2PA'] += PA2

                # Find the matchup player
                opponent_team = 'team2' if player_team == 'team1' else 'team1'
                position = player.get('position')
                matchup_player = players_by_team_and_position[opponent_team].get(position, [{}])[0]
                matchup_name = matchup_player.get('name', '').lower()

                timestamp = datetime.now().isoformat()
                player_data = self.prepare_player_data(player, result, matchup_name, timestamp, hash_value, PM2, PA2)
                sheet = self.f_db_sheet if (player_team == 'team1' and is_team1_friendly) or (player_team == 'team2' and is_team2_friendly) else self.o_db_sheet
                self.log_data_to_sheet(sheet, player_data)

            self.log_game_data(team1_name, team2_name, team1_quarters, team2_quarters, team1_total, team2_total, team1_stats, team2_stats, is_team1_friendly, hash_value)
            self.next_game_id += 1

    def initialize_team_stats(self):
        return {
            'rebounds': 0, 'assists': 0, 'steals': 0, 'blocks': 0,
            'fouls': 0, 'tos': 0, 'FGM': 0, 'FGA': 0, '3PM': 0, '3PA': 0,
            '2PM': 0, '2PA': 0, 'FTM': 0, 'FTA': 0
        }

    def calculate_player_stats(self, player):
        FGM = int(player.get('FGM', 0))
        PM3 = int(player.get('3PM', 0))
        FGA = int(player.get('FGA', 0))
        PA3 = int(player.get('3PA', 0))
        PM2 = FGM - PM3
        PA2 = FGA - PA3
        return PM2, PA2

    def prepare_player_data(self, player, result, matchup_name, timestamp, hash_value, PM2, PA2):
        return [
            self.next_game_id,
            player.get('team', ''),
            player.get('player_number', ''),
            player.get('name', '').lower(),
            player.get('position', ''),
            player.get('grade', ''),
            player.get('points', ''),
            player.get('rebounds', ''),
            player.get('assists', ''),
            player.get('steals', ''),
            player.get('blocks', ''),
            player.get('fouls', ''),
            player.get('tos', ''),
            player.get('FGM', ''),
            player.get('FGA', ''),
            player.get('3PM', ''),
            player.get('3PA', ''),
            PM2,
            PA2,
            player.get('FTM', ''),
            player.get('FTA', ''),
            result,
            matchup_name,
            timestamp,
            hash_value
        ]

    def log_game_data(self, team1_name, team2_name, team1_quarters, team2_quarters, team1_total, team2_total, team1_stats, team2_stats, is_team1_friendly, hash_value):
        if is_team1_friendly:
            team_f_name, team_o_name = team1_name, team2_name
            team_f_quarters, team_o_quarters = team1_quarters, team2_quarters
            team_f_total, team_o_total = team1_total, team2_total
            team_f_stats, team_o_stats = team1_stats, team2_stats
        else:
            team_f_name, team_o_name = team2_name, team1_name
            team_f_quarters, team_o_quarters = team2_quarters, team1_quarters
            team_f_total, team_o_total = team2_total, team1_total
            team_f_stats, team_o_stats = team2_stats, team1_stats

        game_data = [
            self.next_game_id,
            team_f_name,
            team_o_name,
            team_f_quarters.get('quarter_1', 0),
            team_o_quarters.get('quarter_1', 0),
            team_f_quarters.get('quarter_2', 0),
            team_o_quarters.get('quarter_2', 0),
            team_f_quarters.get('quarter_3', 0),
            team_o_quarters.get('quarter_3', 0),
            team_f_quarters.get('quarter_4', 0),
            team_o_quarters.get('quarter_4', 0),
            team_f_total,
            team_o_total,
            team_f_stats['rebounds'],
            team_o_stats['rebounds'],
            team_f_stats['assists'],
            team_o_stats['assists'],
            team_f_stats['steals'],
            team_o_stats['steals'],
            team_f_stats['blocks'],
            team_o_stats['blocks'],
            team_f_stats['fouls'],
            team_o_stats['fouls'],
            team_f_stats['tos'],
            team_o_stats['tos'],
            team_f_stats['FGM'],
            team_o_stats['FGM'],
            team_f_stats['FGA'],
            team_o_stats['FGA'],
            team_f_stats['3PM'],
            team_o_stats['3PM'],
            team_f_stats['3PA'],
            team_o_stats['3PA'],
            team_f_stats['2PM'],
            team_o_stats['2PM'],
            team_f_stats['2PA'],
            team_o_stats['2PA'],
            team_f_stats['FTM'],
            team_o_stats['FTM'],
            team_f_stats['FTA'],
            team_o_stats['FTA'],
            datetime.now().isoformat(),
            hash_value
        ]
        self.log_data_to_sheet(self.game_db_sheet, game_data)

    def process_json_files(self):
        for filename in os.listdir(TO_PROCESS_FOLDER):
            if filename.endswith('_results.json'):
                file_path = os.path.join(TO_PROCESS_FOLDER, filename)
                self.process_json_file(file_path)
                processed_file_path = os.path.join(PROCESSED_FOLDER, filename)
                shutil.move(file_path, processed_file_path)
                print(f"Moved processed file to {PROCESSED_FOLDER}")

def main():
    client = GoogleSheetsClient()
    processor = GameDataProcessor(client)
    processor.process_json_files()

if __name__ == "__main__":
    main()