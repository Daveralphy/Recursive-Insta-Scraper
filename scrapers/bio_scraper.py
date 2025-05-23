import time
import random
import re
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

# Country code mapping for WhatsApp numbers
COUNTRY_CODES = {
    "+1": "United States/Canada",
    "+44": "United Kingdom",
    "+234": "Nigeria",
    "+55": "Brazil",
    "+91": "India",
    # Add more country codes as needed
}

def extract_whatsapp_number(bio_text):
    """Extracts WhatsApp number from bio using regex."""
    phone_pattern = r"\+?\d[\d -]{8,14}\d"
    phone_match = re.findall(phone_pattern, bio_text)
    
    if phone_match:
        number = phone_match[0]
        country = COUNTRY_CODES.get(number[:3], "Unknown")  # Lookup country from country code
        return number, country
    return "", ""

def get_bio_data(driver, username):
    """Extracts bio, external links, and WhatsApp number with region from a user's Instagram profile."""
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    try:
        print(f"📜 Scraping bio data for {username}...")

        wait = WebDriverWait(driver, 10)

        # Extract Bio Text (Below the full name)
        try:
            bio_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header/section/div/span")))
            bio_text = bio_element.text.strip() if bio_element else ""
        except:
            bio_text = ""

        # Extract External Link (Only if present)
        try:
            external_link_element = driver.find_elements(By.XPATH, "//header/section/div/a")
            external_link = external_link_element[0].get_attribute("href") if external_link_element else ""
        except:
            external_link = ""

        # Extract WhatsApp Number & Determine Region
        whatsapp_number, region = extract_whatsapp_number(bio_text)

        return {
            "Username": username,
            "Bio": bio_text,
            "WhatsApp Number": whatsapp_number,
            "Region": region,
            "External Link": external_link if "instagram.com" not in external_link else "",  # Prevent profile URL from being saved as external link
            "Profile URL": profile_url
        }
    except Exception as e:
        print(f"❌ Failed to scrape bio for {username}: {e}")
        return {}

def scrape_bios(driver, usernames):
    """Scrapes bios for given usernames and returns structured data."""
    bios = []

    for username in usernames:
        bio_data = get_bio_data(driver, username)
        if bio_data:
            bios.append(bio_data)

    return bios  # Returns extracted bio details for further use
