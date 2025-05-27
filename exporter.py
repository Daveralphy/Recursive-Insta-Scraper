import os
import pandas as pd
# import gspread # Commented out
# from oauth2client.service_account import ServiceAccountCredentials # Commented out
# from airtable import Airtable # Commented out
import time
from dotenv import load_dotenv

# Load environment variables (for Airtable and Google Sheets credentials)
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)

def export_data(df, config):
    """
    Exports the DataFrame to various formats based on config settings.

    Args:
        df (pd.DataFrame): The DataFrame containing the scraped and classified data.
        config (dict): The loaded configuration dictionary from config.yaml.
    """
    print("\n--- Exporting Final Data (Step 6) ---")

    export_settings = config.get("export_settings", {})
    enabled_formats = export_settings.get("enabled_formats", ["csv"])
    output_dir = "data"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- CSV Export ---
    if "csv" in enabled_formats:
        try:
            csv_filename = export_settings.get("csv_filename", "instagram_leads.csv")
            output_path = os.path.join(output_dir, csv_filename)
            df.to_csv(output_path, index=False)
            print(f"✅ Data successfully exported to CSV: {output_path}")
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")

    # --- Excel Export ---
    # This remains active as it does not require external credentials beyond openpyxl
    if "excel" in enabled_formats:
        try:
            excel_filename = export_settings.get("excel_filename", "instagram_leads.xlsx")
            output_path = os.path.join(output_dir, excel_filename)
            df.to_excel(output_path, index=False)
            print(f"✅ Data successfully exported to Excel: {output_path}")
        except Exception as e:
            print(f"❌ Error exporting to Excel: {e}")

    # --- Airtable Export ---
    # This section is commented out by default.
    # To enable Airtable export:
    # 1. Uncomment the 'import Airtable' line at the top of this file.
    # 2. Uncomment the entire 'if "airtable" in enabled_formats:' block below.
    # 3. Ensure 'airtable' is enabled in 'enabled_formats' in config.yaml.
    # 4. Add your AIRTABLE_API_KEY and AIRTABLE_BASE_ID to your .env file.
    if "airtable" in enabled_formats:
        print("ℹ️ Airtable export code is commented out in exporter.py. Please uncomment it to enable this feature.")
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
        #         print(f"🔄 Attempting to export to Airtable table: '{table_name}'...")
        #         airtable = Airtable(base_id, api_key)
                
        #         # Option 1: Delete existing records and re-upload (simpler for fresh export)
        #         existing_records = airtable.get_all()
        #         if existing_records:
        #             print(f"    Deleting {len(existing_records)} existing records in Airtable...")
        #             # Batch delete for efficiency and to respect rate limits
        #             record_ids_to_delete = [record['id'] for record in existing_records]
        #             delete_batch_size = 10 # Airtable's batch delete limit
        #             for i in range(0, len(record_ids_to_delete), delete_batch_size):
        #                 batch_ids = record_ids_to_delete[i:i + delete_batch_size]
        #                 airtable.batch_delete(batch_ids)
        #                 print(f"    Deleted batch {int(i/delete_batch_size) + 1}/{(len(record_ids_to_delete) + delete_batch_size - 1) // delete_batch_size} from Airtable.")
        #                 time.sleep(0.1) # Small delay to avoid hitting rate limits too hard

        #         # Prepare records for Airtable
        #         records_to_create = df.to_dict(orient='records')
                
        #         # Airtable API has a limit of 10 records per batch for creation
        #         create_batch_size = 10
        #         for i in range(0, len(records_to_create), create_batch_size):
        #             batch = records_to_create[i:i + create_batch_size]
        #             airtable.batch_create(batch)
        #             print(f"    Uploaded batch {int(i/create_batch_size) + 1}/{(len(records_to_create) + create_batch_size - 1) // create_batch_size} to Airtable.")
        #             time.sleep(0.3) # Small delay to respect rate limits

        #         print(f"✅ Data successfully exported to Airtable table: '{table_name}'")

        #     except Exception as e:
        #         print(f"❌ Error exporting to Airtable: {e}")
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
        #         print(f"🔄 Attempting to export to Google Sheet: '{sheet_name}'...")
        #         # Authenticate
        #         scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        #         creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        #         client = gspread.authorize(creds)

        #         # Open the spreadsheet by ID
        #         spreadsheet = client.open_by_id(spreadsheet_id)
        #         worksheet = spreadsheet.worksheet(sheet_name)

        #         # Clear existing data
        #         worksheet.clear()

        #         # Update with headers and data
        #         data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
                
        #         worksheet.update(data_to_upload)
                
        #         print(f"✅ Data successfully exported to Google Sheet: '{spreadsheet.title}' (Worksheet: '{sheet_name}')")

        #     except FileNotFoundError:
        #         print(f"❌ Error: Google Sheets credentials file not found at '{credentials_file}'. Please check the path.")
        #     except gspread.exceptions.SpreadsheetNotFound:
        #         print(f"❌ Error: Google Sheet with ID '{spreadsheet_id}' not found. Check the ID and sharing permissions.")
        #     except gspread.exceptions.WorksheetNotFound:
        #         print(f"❌ Error: Worksheet named '{sheet_name}' not found in the spreadsheet. Check the sheet name.")
        #     except Exception as e:
        #         print(f"❌ Error exporting to Google Sheets: {e}")
        #         print("    Please ensure your service account has Editor access to the Google Sheet and check all IDs/paths.")