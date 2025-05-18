import csv
import os

# For Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# For Airtable
import requests

def export_to_csv(data, filename="output.csv"):
    if not data:
        print("No data to export.")
        return

    headers = [
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

    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for profile in data:
            writer.writerow({key: profile.get(key, "") for key in headers})

    print(f"Exported {len(data)} profiles to {filename}")

def export_to_google_sheets(data, spreadsheet_name, credentials_json_path):
    if not data:
        print("No data to export.")
        return

    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_json_path, scopes=scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open(spreadsheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(spreadsheet_name).sheet1
        # Share the sheet with your email or make it accessible as needed here

    headers = [
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

    sheet.clear()
    sheet.append_row(headers)

    for profile in data:
        row = [profile.get(key, "") for key in headers]
        sheet.append_row(row)

    print(f"Exported {len(data)} profiles to Google Sheets: {spreadsheet_name}")

def export_to_airtable(data, base_id, table_name, api_key):
    if not data:
        print("No data to export.")
        return

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for profile in data:
        fields = {
            "Username": profile.get("Username", ""),
            "Full Name": profile.get("Full Name", ""),
            "Bio": profile.get("Bio", ""),
            "WhatsApp Number": profile.get("WhatsApp Number", ""),
            "WhatsApp Group Link": profile.get("WhatsApp Group Link", ""),
            "Type": profile.get("Type", ""),
            "Region": profile.get("Region", ""),
            "Follower Count": profile.get("Follower Count", ""),
            "Profile URL": profile.get("Profile URL", ""),
            "External Link": profile.get("External Link", "")
        }
        data_json = {"fields": fields}
        response = requests.post(url, json=data_json, headers=headers)
        if response.status_code != 201:
            print(f"Failed to add record for {fields['Username']}: {response.text}")

    print(f"Exported {len(data)} profiles to Airtable table: {table_name}")

import pandas as pd

def export_results(profiles, export_format="excel", filename="results"):
    """
    Export the scraped and classified profiles to Excel or CSV.

    Args:
        profiles (list of dict): The profiles to export.
        export_format (str): 'excel' or 'csv'.
        filename (str): Name of the file (without extension).
    """
    df = pd.DataFrame(profiles)

    if export_format == "excel":
        df.to_excel(f"{filename}.xlsx", index=False)
    elif export_format == "csv":
        df.to_csv(f"{filename}.csv", index=False)
    else:
        raise ValueError("Unsupported export format. Choose 'excel' or 'csv'.")
