import time
import random
import re
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Load configuration
# Assuming config.yaml is in the root directory accessible from where main.py runs
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    # Provide default values if config.yaml is not found
    config = {
        "settings": {"delay_min": 5, "delay_max": 10},
        # user_agents are not directly used in this file but might be in setup_driver in main
    }

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

# Country code mapping for WhatsApp numbers, expanded for LATAM focus
COUNTRY_CODES = {
    "+1": "United States/Canada",
    "+44": "United Kingdom",
    "+234": "Nigeria",
    "+55": "Brazil",
    "+91": "India",
    "+52": "Mexico",
    "+54": "Argentina",
    "+56": "Chile",
    "+57": "Colombia",
    "+51": "Peru",
    "+593": "Ecuador",
    "+591": "Bolivia",
    "+598": "Uruguay",
    "+595": "Paraguay",
    "+502": "Guatemala",
    "+503": "El Salvador",
    "+504": "Honduras",
    "+505": "505 Nicaragua",
    "+506": "Costa Rica",
    "+507": "Panama",
    "+53": "Cuba",
    "+58": "Venezuela",
    # Add more country codes as needed, especially for other LATAM countries
}

def extract_whatsapp_number_and_region(bio_text):
    """
    Extracts a potential WhatsApp number from bio text using regex
    and attempts to determine the region based on the country code.
    """
    # This regex is more robust for various international phone number formats.
    # It looks for a plus sign, followed by 1-3 digits (country code),
    # then optional spaces/hyphens/parentheses, and 8-15 more digits.
    phone_pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,15}"
    phone_match = re.search(phone_pattern, bio_text) # Use re.search to find the first match

    whatsapp_number = ""
    region = ""

    if phone_match:
        number = phone_match.group(0).strip()
        whatsapp_number = number

        # Attempt to find country code at the beginning of the number
        for code, country_name in COUNTRY_CODES.items():
            if number.startswith(code):
                region = country_name
                break
        else:
            # If no specific country code match, try to infer from common LATAM patterns
            # This is a very basic inference and might not be accurate
            if any(c in bio_text.lower() for c in ["latam", "latin america", "mexico", "colombia", "argentina", "chile", "peru", "brazil"]):
                region = "LATAM (Inferred)"
            elif not region: # If still no region, mark as unknown
                region = "Unknown"

    return whatsapp_number, region

def get_bio_data(driver, username):
    """
    Extracts bio, external link, WhatsApp number, and inferred region
    from a user's Instagram profile using a pre-logged-in WebDriver instance.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"📜 Scraping bio data for {username} from: {profile_url}")
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX)) # Add delay after navigating to profile

    bio_data = {
        "Username": username,
        "Bio": "",
        "WhatsApp Number": "",
        "Region": "",
        "External Link": "",
        "Profile URL": profile_url # Keep Profile URL for merging in main.py
    }

    try:
        wait = WebDriverWait(driver, 15) # Increased wait time for initial page load

        # Initial wait for a common element in the profile header
        # This ensures the page has loaded sufficiently before attempting to scrape
        wait.until(EC.presence_of_element_located((By.XPATH, "//header//h2")))
        print(f"  Profile page for {username} loaded for bio scraping.")

        # Extract Bio Text
        try:
            # This XPath targets a common container for the bio text.
            # Instagram often uses a div with specific class names for the bio.
            bio_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x7a106z') and contains(@class, 'x972fbf') and contains(@class, 'xcfux6l')]")))
            bio_data["Bio"] = bio_element.text.strip()
        except TimeoutException:
            print(f"  Bio element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Bio not found for {username}. (XPath might be outdated)")

        # Extract External Link
        try:
            # External link is typically an <a> tag with target="_blank" and rel="nofollow".
            # It's usually found within the profile header area.
            external_link_element = driver.find_element(By.XPATH, "//a[contains(@target, '_blank') and contains(@rel, 'nofollow')]")
            external_link = external_link_element.get_attribute("href")
            # Prevent profile URL from being saved as external link
            bio_data["External Link"] = external_link if "instagram.com" not in external_link else ""
        except NoSuchElementException:
            print(f"  External link not found for {username}. (XPath might be outdated)")

        # Extract WhatsApp Number & Determine Region
        whatsapp_number, region = extract_whatsapp_number_and_region(bio_data["Bio"])
        bio_data["WhatsApp Number"] = whatsapp_number
        bio_data["Region"] = region

        print(f"✅ Scraped bio data for {username}:")
        for key, value in bio_data.items():
            print(f"    {key}: {value}")

    except TimeoutException:
        print(f"❌ Timeout while loading page for {username}. Page might not have loaded correctly or selectors are wrong.")
        print("  Current page source for debugging (first 2000 chars):")
        print(driver.page_source[:2000]) # Print first 2000 characters of page source for debugging
    except Exception as e:
        print(f"❌ An unexpected error occurred while scraping bio for {username}: {e}")

    return bio_data

def scrape_bios(driver, usernames):
    """Scrapes bios for given usernames and returns structured data."""
    bios = []

    for username in usernames:
        bio_data = get_bio_data(driver, username)
        if bio_data:
            bios.append(bio_data)
        # Introduce a random delay between requests to avoid rate limiting
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    return bios # Returns extracted bio details for further use
