## Automate 2k

### Project Overview

This project consists of two main Python scripts, `automate_sheet.py` and `automate_2k.py`, designed to automate the process of extracting game data from images and logging it into Google Sheets. The project uses OCR (Optical Character Recognition) to read data from images and then processes and logs this data into Google Sheets for further analysis.

This will not work on pictures of your TV! This is meant for screenshots downloaded specifically from the PSN app! You can try to use Xbox screenshots but they will more than likely extract inaccurate data.

### Features

- **OCR Processing**: Extracts player and team statistics from game images.
  - Not camera pictures. You need literal screenshots extracted from the PSN app.
- **Google Sheets Integration**: Logs the extracted data into specified Google Sheets.
- **Exponential Backoff**: Handles API rate limits *relatively* gracefully.

### Issues

- The lower quality the screenshot, the worse the script will process the data. 
- Xbox screenshots basically don't process at all. It really hates the teammate grades specifically. Xbox does some special processing that makes the OCR hate it.
- Names will regularly have characters like `3`, `a`, `5`, and `b` attached to the end. These should be manually removed.
- OCR takes a long time to run.

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.6 or higher
  - Install via the Microsoft Store
- Google Cloud account with access to Google Sheets API
  - Detailed instructions available below
- Required Python packages (listed below)
- Copy of the [spreadsheet](https://docs.google.com/spreadsheets/d/1BdKratD66zybUj2ncnw_ySrfJcnXbnq1eHe51ljUK7k/edit?gid=0#gid=0)
  - Once the spreadsheet is copied (File > Make a Copy):
  - Copy the `Template` sheet for each player you want to track
  - Rename that sheet, and in the `SHEET DB` sheet, rename the first row to whatever you renamed the sheet to. The value in `A2` should be the player's username found in `F DB`
  - For each player you want to add, you will have to copy the entire row in `SHEET DB` and paste it below.

### Setting Up Google Cloud for Google Sheets API

1. **Create a Google Cloud Project**

   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Click on the project dropdown at the top of the page and select "New Project".
   - Enter a project name and click "Create".

2. **Enable the Google Sheets API**

   - In the Google Cloud Console, go to the "APIs & Services" > "Library".
   - Search for "Google Sheets API".
   - Click on "Google Sheets API" and then click "Enable".

3. **Enable the Google Drive API**

   - In the Google Cloud Console, go to the "APIs & Services" > "Library".
   - Search for "Google Drive API".
   - Click on "Google Drive API" and then click "Enable".

4. **Create Credentials**

   - Go to "APIs & Services" > "Credentials".
   - Click on "Create Credentials" and select "OAuth 2.0 Client IDs".
   - Configure the consent screen by providing the necessary information.
   - After configuring the consent screen, select "Application type" as "Desktop app" and click "Create".
   - Download the `credentials.json` file and save it to your project root directory.

### Installation

1. **Download the ZIP**

   Open your web browser and go to the URL: https://github.com/wokaa/automate-2k/archive/refs/heads/main.zip

2. **Extract the ZIP File**

   - Locate the downloaded ZIP file on your computer.
   - Right-click on the ZIP file and select "Extract All...".
   - Choose a destination folder and click "Extract".

3. **Navigate to the Extracted Folder**

   Open a command prompt or terminal and navigate to the extracted folder:
   ```sh
   cd path\to\extracted-folder
   ```

4. **Set Up Virtual Environment**

   Create and activate a virtual environment:

   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

5. **Install Dependencies**

   Install the required Python packages:

   ```sh
   pip install -r requirements.txt
   ```

   The `requirements.txt` file should include:

   ```txt
   gspread
   google-auth
   google-auth-oauthlib
   google-auth-httplib2
   easyocr
   numpy
   pillow
   torch
   opencv-python
   ```

6. **Google Sheets API Setup**

   - Enable the Google Sheets API and Google Drive API in your Google Cloud Console.
   - Download the `credentials.json` file and place it in the project root directory.
   - Run the script to generate the `token.json` file for authentication:

     ```sh
     python automate_sheet.py
     ```

### Usage

1. **Prepare Input Data**

   - Place the game images in the `./toProcess/images/` directory.
   - Ensure the images are named appropriately (e.g., `game1.png`, `game2.jpg`).

2. **Run the OCR Processor**

   Execute the `automate_2k.py` script to process the images and generate JSON files:

   ```sh
   python automate_2k.py
   ```

   This script will:
   - Extract data from the images using OCR.
   - Save the extracted data as JSON files in the `./toProcess/json/` directory.
   - Move the processed images to the `./processed/images/` directory.

3. **Log Data to Google Sheets**

   Execute the `automate_sheet.py` script to log the extracted data into Google Sheets:

   ```sh
   python automate_sheet.py
   ```

   This script will:
   - Read the JSON files from the `./toProcess/json/` directory.
   - Log the data into the specified Google Sheets.
     - It will ask you which team is the friendly team (i.e., the team YOU played on). This is important, take your time.
   - Move the processed JSON files to the `./processed/json/` directory.

### Configuration

- **Google Sheets Configuration**: Update the `SPREADSHEET_NAME`, `F_DB_SHEET`, `O_DB_SHEET`, and `GAME_DB_SHEET` constants in `automate_sheet.py` with your Google Sheets details.
  - You should only need to update the `SPREADSHEET_NAME`, to whatever the name of your spreadsheet is.
- **Image and JSON Directories**: Ensure the directories `./toProcess/images/`, `./toProcess/json/`, `./processed/images/`, and `./processed/json/` exist.
- Update the `correct_common_errors` function with commonly occurring username errors.
  - For example, `Al Player` is being transformed to `AI Player`.

### Troubleshooting

- **Authentication Issues**: Ensure your `credentials.json` and `token.json` files are correctly set up.
- **OCR Accuracy**: Adjust the OCR settings or preprocess the images for better accuracy.
- **API Rate Limits**: The script uses exponential backoff to handle rate limits. If you encounter issues, try increasing the delay or reducing the number of requests.

### Contributing

Contributions are welcome. This project was quickly patched together for the NBA 2k25 cycle, and a lot of Copilot was used. It's messy at best.

### License

This project is licensed under the GNU General Public License.

### Acknowledgements

- [Google Sheets API](https://developers.google.com/sheets/api)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [OpenCV](https://opencv.org/)
- [PyTorch](https://pytorch.org/)

---

Feel free to reach out if you have any questions or need further assistance. Happy coding!