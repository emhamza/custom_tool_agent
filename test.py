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

#=================================================
# def browse_medium_article(url: str) -> str:
#     """
#     Fetches the main textual content of a given Medium article URL.
#     This tool is designed to read and summarize specific articles.
#     """

#     try:
#         response = requests.get(url, timeout=15)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.text, 'html.parser')

#         # Attempt to find the main article content. Medium articles are often within <article> tags.
#         # Fallback to common content tags or body if <article> is not found.
#         main_content_tag = soup.find('article') or soup.find('main') or soup.find('section') or soup.body
        
#         if main_content_tag:
#             text = main_content_tag.get_text(separator=' ').strip()
#             text = ' '.join(text.split()) # Normalize whitespace
#         else:
#             text = "Could not identify a main content area. Returning full body text."
#             text = ' '.join(soup.body.get_text(separator=' ').split()) # type: ignore
        
#         #return the substantial portion fo the content
#         return text[:4000]
#     except requests.exceptions.RequestException as e:
#         return f"Error fetching url: {e}. Please ensure the url is valid and accessible"
#     except Exception as e:
#         return f"An unexpected error occured during browsing: {e}"
    
# medium_browsing_tool = StructuredTool.from_function(
#     func=browse_medium_article,
#     name="medium_article_reader",
#     description="Useful for when you need to read the full content of specific medium article"
# )
