import csv
import os

# Column order and headers as required
HEADERS = [
    "Username",
    "Full Name",
    "Bio",
    "WhatsApp Number",
    "WhatsApp Group Link",
    "Type",
    "Region",
    "Follower Count",
    "Profile URL",
    "External Link"
]

def export_to_csv(profiles, output_file="exported_profiles.csv"):
    """
    Exports the list of profile dictionaries to a CSV file.

    Args:
        profiles (list of dict): Profile data to export.
        output_file (str): Path to the CSV output file.

    Returns:
        str: Path to the CSV file created.
    """
    if not profiles:
        print("No data found to export.")
        return None

    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS, extrasaction='ignore')
        writer.writeheader()
        for profile in profiles:
            # Ensure all keys exist, fallback to empty string if missing
            row = {key: profile.get(key.lower().replace(" ", "_"), "") for key in HEADERS}
            writer.writerow(row)

    print(f"Exported {len(profiles)} profiles to {output_file}")
    return os.path.abspath(output_file)

def export_to_google_sheets(profiles, spreadsheet_id, credentials_json):
    """
    Placeholder for Google Sheets export functionality.

    Args:
        profiles (list of dict): Profile data to export.
        spreadsheet_id (str): ID of the Google Sheets spreadsheet.
        credentials_json (str): Path to Google API credentials JSON.

    Returns:
        bool: True if export successful, False otherwise.
    """
    # TODO: Implement using Google Sheets API
    print("Google Sheets export not implemented yet.")
    return False

def export_to_airtable(profiles, base_id, table_name, api_key):
    """
    Placeholder for Airtable export functionality.

    Args:
        profiles (list of dict): Profile data to export.
        base_id (str): Airtable base ID.
        table_name (str): Airtable table name.
        api_key (str): Airtable API key.

    Returns:
        bool: True if export successful, False otherwise.
    """
    # TODO: Implement using Airtable API
    print("Airtable export not implemented yet.")
    return False
