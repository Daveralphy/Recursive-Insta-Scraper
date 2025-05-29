import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from airtable import Airtable
import time
from dotenv import load_dotenv
import openpyxl # NEW: Import openpyxl for Excel appending

# Load environment variables (for Airtable and Google Sheets credentials)
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)

# This set will keep track of which usernames have already been exported
# to prevent duplicates when using append mode.
# Note: In a multi-process/multi-thread scenario, this would need to be shared.
# For a single-threaded script, it's fine here, but conceptually might be better in main.py
# and passed around or managed by a higher-level object.
# However, for simple append, managing headers per file is more critical.

def export_data_live(new_profiles_data_list, config):
    """
    Exports a list of new profile data dictionaries to various formats,
    appending to existing files/databases.

    Args:
        new_profiles_data_list (list): A list of dictionaries, each representing a classified profile.
        config (dict): The loaded configuration dictionary from config.yaml.
    """
    if not new_profiles_data_list:
        return # Do nothing if no new data to export

    df_to_export = pd.DataFrame(new_profiles_data_list)
    
    export_settings = config.get("export_settings", {})
    enabled_formats = export_settings.get("enabled_formats", ["csv"])
    output_dir = "data"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"\n--- Live Exporting {len(new_profiles_data_list)} new data points ---")

    # --- CSV Export ---
    if "csv" in enabled_formats:
        try:
            csv_filename = export_settings.get("csv_filename", "instagram_leads.csv")
            output_path = os.path.join(output_dir, csv_filename)
            
            # Check if file exists to determine if header is needed
            file_exists = os.path.exists(output_path)
            
            df_to_export.to_csv(output_path, mode='a', header=not file_exists, index=False)
            print(f"✅ Appended data to CSV: {output_path}")
        except Exception as e:
            print(f"❌ Error appending to CSV: {e}")

    # --- Excel Export ---
    # This section is enabled by default as it only requires openpyxl.
    # To enable Excel export:
    # 1. Ensure 'openpyxl' is installed (`pip install openpyxl`).
    # 2. Ensure 'excel' is enabled in 'enabled_formats' in config.yaml.
    if "excel" in enabled_formats:
        try:
            excel_filename = export_settings.get("excel_filename", "instagram_leads.xlsx")
            output_path = os.path.join(output_dir, excel_filename)
            
            wb = None
            if not os.path.exists(output_path):
                # Create a new workbook if file doesn't exist and write header
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Instagram Leads" # Set sheet title
                ws.append(df_to_export.columns.tolist()) # Write header row
            else:
                # Load existing workbook
                wb = openpyxl.load_workbook(output_path)
                ws = wb.active # Get the active sheet

            # Append each row of the new data
            for r_idx, row in df_to_export.iterrows():
                ws.append(row.tolist())
            
            wb.save(output_path)
            print(f"✅ Appended data to Excel: {output_path}")
        except Exception as e:
            print(f"❌ Error appending to Excel: {e}")


    # --- Airtable Export ---
    # This section is commented out by default.
    # To enable Airtable export:
    # 1. Uncomment the 'import Airtable' line at the top of this file.
    # 2. Uncomment the entire 'if "airtable" in enabled_formats:' block below.
    # 3. Ensure 'airtable' is enabled in 'enabled_formats' in config.yaml.
    # 4. Add your AIRTABLE_API_KEY and AIRTABLE_BASE_ID to your .env file.
    if "airtable" in enabled_formats:
        print("ℹ️ Airtable export code is commented out in exporter.py. Please uncomment it to enable this feature.")
        # from airtable import Airtable # Moved import here to keep main import section clean if uncommented
        # # Get credentials from environment variables
        # api_key = os.getenv("AIRTABLE_API_KEY")
        # base_id = os.getenv("AIRTABLE_BASE_ID")
        
        # # Get table name from config.yaml (since it's specific to the project)
        # airtable_config = export_settings.get("airtable", {})
        # table_name = airtable_config.get("table_name")

        # if not all([api_key, base_id, table_name]):
        #     print("❌ Airtable export skipped: Missing AIRTABLE_API_KEY, AIRTABLE_BASE_ID in .env or Table Name in config.yaml. Please check your setup.")
        # else:
        #     try:
        #         airtable = Airtable(base_id, api_key)
                
        #         # Prepare records for Airtable
        #         records_to_create = df_to_export.to_dict(orient='records')
                
        #         # Airtable API has a limit of 10 records per batch for creation
        #         create_batch_size = 10
        #         for i in range(0, len(records_to_create), create_batch_size):
        #             batch = records_to_create[i:i + create_batch_size]
        #             airtable.batch_create(batch)
        #             time.sleep(0.3) # Small delay to respect rate limits

        #         print(f"✅ Appended data to Airtable table: '{table_name}'")

        #     except Exception as e:
        #         print(f"❌ Error appending to Airtable: {e}")
        #         print("    Please ensure your Airtable API Key, Base ID in .env and Table Name in config.yaml are correct.")
        #         print("    Also, check if the column names in your DataFrame match those in Airtable.")


    # --- Google Sheets Export ---
    # This section is commented out by default.
    # To enable Google Sheets export:
    # 1. Uncomment the 'import gspread' and 'from oauth2client...' lines at the top of this file.
    # 2. Uncomment the entire 'if "google_sheets" in enabled_formats:' block below.
    # 3. Ensure 'google_sheets' is enabled in 'enabled_formats' in config.yaml.
    # 4. Complete the Google Sheets API setup (service account, JSON file) and add
    #    your GOOGLE_SHEETS_SPREADSHEET_ID to your .env file.
    if "google_sheets" in enabled_formats:
        print("ℹ️ Google Sheets export code is commented out in exporter.py. Please uncomment it to enable this feature.")
        # import gspread # Moved import here to keep main import section clean if uncommented
        # from oauth2client.service_account import ServiceAccountCredentials # Moved import here
        # gsheets_config = export_settings.get("google_sheets", {})
        # credentials_file = gsheets_config.get("credentials_file")
        
        # # Get spreadsheet ID from environment variable
        # spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        
        # # Get sheet name from config.yaml
        # sheet_name = gsheets_config.get("sheet_name")

        # if not all([credentials_file, spreadsheet_id, sheet_name]):
        #     print("❌ Google Sheets export skipped: Missing credentials file or Sheet Name in config.yaml, or GOOGLE_SHEETS_SPREADSHEET_ID in .env. Please check your setup.")
        #     print("    Refer to the setup instructions for Google Sheets API.")
        # else:
        #     try:
        #         # Authenticate
        #         scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        #         creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        #         client = gspread.authorize(creds)

        #         # Open the spreadsheet by ID
        #         spreadsheet = client.open_by_id(spreadsheet_id)
        #         worksheet = spreadsheet.worksheet(sheet_name)

        #         # Check if sheet is empty to write header
        #         current_values = worksheet.get_all_values()
        #         if not current_values: # Sheet is empty, write header first
        #             worksheet.append_row(df_to_export.columns.tolist())

        #         # Append data rows
        #         for r_idx, row in df_to_export.iterrows():
        #             worksheet.append_row(row.tolist())
        #             time.sleep(0.1) # Small delay for API rate limits
                
        #         print(f"✅ Appended data to Google Sheet: '{spreadsheet.title}' (Worksheet: '{sheet_name}')")

        #     except FileNotFoundError:
        #         print(f"❌ Error: Google Sheets credentials file not found at '{credentials_file}'. Please check the path.")
        #     except gspread.exceptions.SpreadsheetNotFound:
        #         print(f"❌ Error: Google Sheet with ID '{spreadsheet_id}' not found. Check the ID and sharing permissions.")
        #     except gspread.exceptions.WorksheetNotFound:
        #         print(f"❌ Error: Worksheet named '{sheet_name}' not found in the spreadsheet. Check the sheet name.")
        #     except Exception as e:
        #         print(f"❌ Error appending to Google Sheets: {e}")
        #         print("    Please ensure your service account has Editor access to the Google Sheet and check all IDs/paths.")