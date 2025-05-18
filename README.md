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
  - scraper/ - Core scraping modules
    - __init__.py
    - followers_scraper.py - Scrapes followers and following lists
    - bio_scraper.py - Scrapes light profile info for filtering
    - profile_scraper.py - Scrapes full profile details
    - whatsapp_detector.py - Detects WhatsApp numbers and group links
    - classifier.py - AI or rule-based business type classification
    - exporter.py - Exports results to CSV, Google Sheets, or Airtable
  - config/
    - config.yaml - Configuration settings (limits, delays, recursion toggle)
  - utils/
    - helpers.py - Utility functions and helpers
  - main.py - Main script to run the bot
  - requirements.txt - Python dependencies list
  - README.md - Project documentation

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
5. Configure your settings in `config/config.yaml`.

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

For questions or collaboration, please reach out via the GitHub repo or the WhatsApp group linked in the project documentation.
