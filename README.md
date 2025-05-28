# LATAM Instagram WhatsApp Scraper Bot

Python-based scraper for discovering Latin American cellphone resellers, distributors, retailers, and repair shops via Instagram. The bot extracts WhatsApp contact info and classifies profiles using AI filtering or keyword logic.

---

## 🚀 Features

- Scrapes followers/following from seed accounts  
- Light scrape with AI or keyword-based filtering (Spanish/Portuguese focus)  
- Full scrape for relevant bios only  
- Detects WhatsApp numbers and group links via regex  
- Classifies accounts: Retailer, Reseller, Distributor, Repair Shop  
- Supports proxy rotation, rate limiting, and recursion  
- Outputs to clean CSV / Airtable / Google Sheets  

---

## 📁 Project Structure

- latam-instagram-whatsapp-scraper/
  - data/ Directory where all exported data files (CSV, Excel) will be saved.
  - scrapers/ - Contains the core Python modules responsible for various scraping and data processing tasks.
    - classifier.py - Handles cleaning scraped profile bios, extracting contact information (like WhatsApp numbers and group links), and classifying profiles based on business type (e.g., Retailer, Distributor).
    - followers_scraper.py - Manages the process of navigating to Instagram profiles, scraping their followers and following lists, and recursively expanding the search to find new relevant leads.
    - profile_scraper.py - Dedicated module for performing a detailed scrape of individual Instagram profiles, collecting comprehensive information such as full name, bio, external links, and follower/following counts.
  - config.yaml - The central configuration file where you can adjust various settings for the scraper, including delays, scraping limits, recursion depth, and export preferences.
  - exporter.py - Responsible for handling the "live export" functionality, writing processed data incrementally to selected output formats like CSV, Excel, Google Sheets, and Airtable.
  - main.py - The primary entry point of the application, orchestrating the entire scraping workflow from login to data processing and export.
  - requirements.txt - Lists all Python package dependencies required for the project, ensuring a consistent development and deployment environment.
  - README.md - This documentation file, providing an overview of the project, setup instructions, and usage guidelines.

---

## Setup Instructions

1. Clone the repository:
`git clone https://github.com/Daveralphy/latam-instagram-whatsapp-scraper.git`
2. Navigate to the project directory:
`cd latam-instagram-whatsapp-scraper`
3. Create and activate a virtual environment:
`python -m venv venv`
`source venv/bin/activate` # On Windows: venv\Scripts\activate
4. Install dependencies:
`pip install -r requirements.txt`
5. Create and configure your .env file:
In the root directory of the project, create a new file named .env (note the leading dot).
6. Paste the following into your .env file

```INSTAGRAM_USERNAME="your_instagram_username"
INSTAGRAM_PASSWORD="your_instagram_password"
OPENAI_API_KEY="your_openai_api_key_here"

# Optional: Airtable Credentials (uncomment and fill if using Airtable export)
# AIRTABLE_API_KEY="keyXXXXXXXXXXXXXX"
# AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"

# Optional: Google Sheets Credentials (uncomment and fill if using Google Sheets export)
# GOOGLE_SHEETS_SPREADSHEET_ID="your_google_sheet_id_here"
```
Important: Keep your .env file secure and do not share it or commit it to version control.

7. Configure your settings in `config.yaml`.
---

## Usage

Run the main script:
`python main.py`

Use the config file to adjust scraping limits, delays, and recursion toggle.

---

## How It Works

- The bot starts by taking initial Instagram usernames from config.yaml. These "seed" accounts act as starting points for a broader search.
- For each seed username, the bot scrapes their followers and following lists. This expansion respects configurable limits or can run in an unlimited mode, as defined in config.yaml. Discovered usernames are managed in a queue, with automatic deduplication.
- New usernames undergo a "light scrape" to quickly extract their public bio, full name, and external link. Using keyword matching (from config.yaml with Spanish/Portuguese focus) and optional AI filtering, irrelevant profiles are quickly filtered. This saves time and helps avoid detection.
- Only profiles that pass the relevance filter receive a full, detailed scrape. The bot extracts comprehensive information including username, full name, cleaned bio, external link, follower count, and profile URL. Regex patterns extract WhatsApp numbers and group links. It also attempts region detection from WhatsApp numbers.
- Each fully scraped and approved profile is classified into business types. Rule-based logic (and optional AI) categorizes profiles as "Retailer," "Reseller," "Distributor," "Repair Shop," or "Phone & Accessories," based on bio content and keywords.
- Processed and classified data is immediately exported. This "live export" writes data to chosen formats as soon as a profile is ready, without waiting for the entire process. The system prevents duplicates, ensuring clean output. Results export to CSV (default), Excel, Google Sheets, or Airtable; the latter two require specific credential setup.

---

## Configuration

All configurable options are found in `config.yaml`. These include:

- Scrape Limits: Control how many followers/following are scraped (e.g., a set number like 500 or unlimited).
- Delay Settings: Adjust the random pause between actions (delay_min and delay_max), with 1-3 seconds generally recommended to avoid detection.
- Recursion Depth: Determine how many levels deep the bot will scrape followers of followers.
- Browser Visibility: Choose to run the browser visibly (visible_browser: true) for debugging or in headless (invisible) mode (visible_browser: false).
- Keywords: A list of terms used for filtering and classifying relevant phone-related profiles.
- Seed Usernames: The initial Instagram profiles from which the scraping process begins.
- User Agents: A list of browser identities the scraper randomly uses for each session to help avoid detection.
- Export Formats: Enable or disable output formats like CSV, Excel, Airtable, and Google Sheets.
- File Naming: Set custom filenames for CSV and Excel exports.
- Airtable/Google Sheets Details: Configure specific table names or credentials for these respective export options.

---

## Output Example

A sample row in the export file contains:

| Username       | Full Name       | Bio                         | WhatsApp Number | WhatsApp Group Link          | Type        | Region    | Follower Count | Profile URL                         | External Link          |
|----------------|-----------------|-----------------------------|-----------------|-----------------------------|-------------|-----------|----------------|------------------------------------|------------------------|
| gsm.latam      | GSM LATAM Store | Venta de celulares y accesorios | +52 1234567890  | https://chat.whatsapp.com/abc | Retailer    | Mexico    | 15000          | https://instagram.com/gsm.latam    | https://gsmstore.com   |

---

## Contribution

- Commit your work daily with clear messages.
- Use a dev branch for daily work.
- Only merge to main after testing and stabilization.
- Keep code clean, modular, and well-commented.

---

## License

This project is licensed under the MIT License.

---

## Contact

For questions or collaboration, please reach out via the GitHub repo or this WhatsApp group linked at https://chat.whatsapp.com/LjycmpBDNL78ZB3cgAcged.
