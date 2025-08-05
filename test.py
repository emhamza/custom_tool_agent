import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# The file name of your downloaded service account credentials JSON file
CREDENTIALS_FILE = 'credentials.json'

# The name of the Google Sheet you created
SHEET_NAME = 'automation_agent'

try:
    # Authenticate using the service account credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope) # type: ignore
    client = gspread.authorize(creds) # type: ignore

    # Open the spreadsheet by its title
    sheet = client.open(SHEET_NAME).sheet1

    # Prepare a new row of data to append
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_data = [f"Test run at {now}", "Setup successful!", "Ready for the agent"]

    # Append the new row to the sheet
    sheet.append_row(test_data)

    print("✅ Success! Data has been written to the Google Sheet.")

except gspread.exceptions.APIError as e:
    print("❌ API Error:", e)
    print("Please ensure the Google Sheets API is enabled and your service account has Editor access to the sheet.")
except FileNotFoundError:
    print("❌ File Not Found Error: credentials.json not found.")
    print("Please make sure your credentials file is named correctly and is in the same directory.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")