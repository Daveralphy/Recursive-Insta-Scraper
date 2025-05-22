import time
import random
import re
import yaml
import pandas as pd
from selenium.webdriver.common.by import By

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
SEED_USERNAMES = config["seed_usernames"]  # Now correctly using seed usernames

def extract_whatsapp_number(bio_text):
    """Extracts WhatsApp number from bio using regex."""
    phone_pattern = r"\+?\d[\d -]{8,14}\d"
    phone_match = re.findall(phone_pattern, bio_text)
    return phone_match[0] if phone_match else ""

def get_bio_data(driver, username):
    """Extracts only the bio section from a user's Instagram profile."""
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    try:
        bio_element = driver.find_elements(By.XPATH, "//header//section//div/span")
        external_link_element = driver.find_elements(By.XPATH, "//header//section//div/a")

        bio_text = bio_element[0].text if bio_element else ""
        external_link = external_link_element[0].get_attribute("href") if external_link_element else ""

        # Extract WhatsApp info
        whatsapp_number = extract_whatsapp_number(bio_text)

        return {
            "Username": username,
            "Bio": bio_text,
            "WhatsApp Number": whatsapp_number,
            "External Link": external_link
        }
    except Exception as e:
        print(f"❌ Failed to scrape bio for {username}: {e}")
        return {}

def scrape_bios(driver):
    """Scrapes bios for the seed usernames defined in the config file."""
    bios = []

    for username in SEED_USERNAMES:
        bio_data = get_bio_data(driver, username)
        if bio_data:
            bios.append(bio_data)

    # Ensure directory exists before saving
    df = pd.DataFrame(bios)
    df.to_csv("data/instagram_bios.csv", index=False)
    print(f"✅ Bio scraping complete! {len(bios)} bios saved to data/instagram_bios.csv")
