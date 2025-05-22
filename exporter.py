import os
import pandas as pd
import yaml

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

EXPORT_TYPE = config.get("settings", {}).get("export_format", "csv")  # Default to CSV
DATA_FOLDER = "data"
OUTPUT_FILENAME = os.path.join(DATA_FOLDER, "exported_data.csv")

# Load scraped CSV files
followers_file = os.path.join(DATA_FOLDER, "instagram_followers.csv")
bios_file = os.path.join(DATA_FOLDER, "instagram_bios.csv")
profiles_file = os.path.join(DATA_FOLDER, "instagram_profiles.csv")

# Read data from CSVs
followers_df = pd.read_csv(followers_file) if os.path.exists(followers_file) else pd.DataFrame(columns=["Username", "Follower Count"])
bios_df = pd.read_csv(bios_file) if os.path.exists(bios_file) else pd.DataFrame(columns=["Username", "Bio", "WhatsApp Number", "WhatsApp Group Link", "Type", "External Link"])
profiles_df = pd.read_csv(profiles_file) if os.path.exists(profiles_file) else pd.DataFrame(columns=["Username", "Full Name", "Region", "Profile URL"])

# Merge datasets based on `Username`
merged_df = profiles_df.merge(bios_df, on="Username", how="outer").merge(followers_df, on="Username", how="outer")

# Ensure all required columns exist
expected_columns = [
    "Username", "Full Name", "Bio", "WhatsApp Number", "WhatsApp Group Link",
    "Type", "Region", "Follower Count", "Profile URL", "External Link"
]

# Check for missing columns and fill with empty values
for col in expected_columns:
    if col not in merged_df.columns:
        merged_df[col] = ""

# Convert numerical columns to strings before filling NaN values
merged_df["Follower Count"] = merged_df["Follower Count"].astype(str)

# Fill missing values with empty strings
merged_df.fillna("", inplace=True)

# Reorder columns properly
merged_df = merged_df[expected_columns]

# Save to CSV
merged_df.to_csv(OUTPUT_FILENAME, index=False)
print(f"✅ Data export complete! File saved as {OUTPUT_FILENAME}")

# Optional: Export to Excel
if EXPORT_TYPE == "xlsx":
    excel_filename = os.path.join(DATA_FOLDER, "exported_data.xlsx")
    merged_df.to_excel(excel_filename, index=False)
    print(f"✅ Data also saved as {excel_filename}")

# Optional: Export to Google Sheets or Airtable (if credentials exist)
if EXPORT_TYPE in ["google_sheets", "airtable"]:
    credentials = config.get("export_credentials", {})
    
    if EXPORT_TYPE == "google_sheets" and "google_sheet_id" in credentials:
        import gspread
        from google.oauth2.service_account import Credentials

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(credentials["google_creds_file"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(credentials["google_sheet_id"]).sheet1
        sheet.clear()
        sheet.append_row(merged_df.columns.tolist())
        for row in merged_df.values.tolist():
            sheet.append_row(row)
        print("✅ Data exported to Google Sheets successfully!")

    if EXPORT_TYPE == "airtable" and "airtable_api_key" in credentials and "airtable_base_id" in credentials:
        import requests
        
        airtable_api_url = f"https://api.airtable.com/v0/{credentials['airtable_base_id']}/exported_data"
        headers = {"Authorization": f"Bearer {credentials['airtable_api_key']}", "Content-Type": "application/json"}
        
        records = [{"fields": dict(zip(merged_df.columns, row))} for row in merged_df.values.tolist()]
        response = requests.post(airtable_api_url, headers=headers, json={"records": records})
        
        if response.status_code == 200:
            print("✅ Data exported to Airtable successfully!")
        else:
            print(f"❌ Airtable export failed: {response.text}")
