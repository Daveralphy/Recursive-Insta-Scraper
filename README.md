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
Add your Instagram login credentials and (optionally) your OpenAI API key to this file, replacing the placeholder values:
Paste the following into your .env file (just as it is)

```INSTAGRAM_USERNAME="your_instagram_username"
INSTAGRAM_PASSWORD="your_instagram_password"
OPENAI_API_KEY="your_openai_api_key_here"

# Optional: Airtable Credentials (uncomment and fill if using Airtable export)
# AIRTABLE_API_KEY="keyXXXXXXXXXXXXXX"
# AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"

# Optional: Google Sheets Credentials (uncomment and fill if using Google Sheets export)
# GOOGLE_SHEETS_SPREADSHEET_ID="your_google_sheet_id_here"

Important: Keep your .env file secure and do not share it or commit it to version control.
5. Configure your settings in `config.yaml`.```

---

## Usage

Run the main script:
`python main.py`

Use the config file to adjust scraping limits, delays, and recursion toggle.

---

## How It Works

- The bot starts by taking a list of seed Instagram usernames.
- It scrapes their followers and following lists, respecting the configured limit.
- For each scraped username, it performs a light scrape of their bio and name.
- Using AI filtering or keyword matching (Spanish and Portuguese keywords), it filters out irrelevant profiles.
- For approved profiles, it performs a full scrape to extract detailed info, including WhatsApp numbers and group links using regex.
- Profiles are classified into business types based on bio content.
- Results are exported cleanly and deduplicated into the chosen output format.

---

## Configuration

All configurable options are found in `config/config.yaml`. These include:

- Scrape limit (e.g., 500 or unlimited)
- Delay between requests (1–3 seconds recommended)
- Recursion toggle to feed found usernames back into scraping
- Proxy settings for rotation

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
