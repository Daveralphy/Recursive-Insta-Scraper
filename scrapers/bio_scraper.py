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
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    config = {"settings": {"delay_min": 5, "delay_max": 10}}

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

# Country code mapping for WhatsApp numbers (LATAM focus)
COUNTRY_CODES = {
    "+1": "United States/Canada", "+44": "United Kingdom", "+234": "Nigeria",
    "+55": "Brazil", "+91": "India", "+52": "Mexico", "+54": "Argentina",
    "+56": "Chile", "+57": "Colombia", "+51": "Peru", "+593": "Ecuador",
    "+591": "Bolivia", "+598": "Uruguay", "+595": "Paraguay", "+502": "Guatemala",
    "+503": "El Salvador", "+504": "Honduras", "+505": "Nicaragua", "+506": "Costa Rica",
    "+507": "Panama", "+53": "Cuba", "+58": "Venezuela"
}

def extract_whatsapp_number_and_region(bio_text):
    """Extracts a WhatsApp number and region from bio text using regex."""
    phone_pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,15}"
    phone_match = re.search(phone_pattern, bio_text)

    whatsapp_number = ""
    region = ""

    if phone_match:
        number = phone_match.group(0).strip()
        whatsapp_number = number

        for code, country_name in COUNTRY_CODES.items():
            if number.startswith(code):
                region = country_name
                break
        else:
            region = "LATAM (Inferred)" if any(c in bio_text.lower() for c in 
                ["latam", "latin america", "mexico", "colombia", "argentina", "chile", "peru", "brazil"]) else "Unknown"

    return whatsapp_number, region

def get_bio_data(driver, username):
    """Extracts full name from the first line of the bio and separates the rest."""
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"📜 Scraping bio data for {username} from: {profile_url}")
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    bio_data = {
        "Username": username, "Full Name": "", "Bio": "", "WhatsApp Number": "",
        "Region": "", "External Link": "", "Profile URL": profile_url
    }

    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, "//header")))

        print(f"  Profile page for {username} loaded for bio scraping.")

        # Extract Bio Text & Separate Full Name
        try:
            bio_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x7a106z')]")))
            bio_text = bio_element.text.strip()
            bio_lines = bio_text.split("\n")

            bio_data["Full Name"] = bio_lines[0] if bio_lines else ""  
            bio_data["Bio"] = "\n".join(bio_lines[1:]) if len(bio_lines) > 1 else ""  

            print(f"  Full name extracted: {bio_data['Full Name']}")
            print(f"  Bio extracted: {bio_data['Bio']}")
        except (TimeoutException, NoSuchElementException):
            print(f"  Bio element not found for {username}. (XPath might be outdated)")

        # Extract External Link
        try:
            external_link_element = driver.find_element(By.XPATH, "//a[contains(@target, '_blank') and contains(@rel, 'nofollow')]")
            external_link = external_link_element.get_attribute("href")
            bio_data["External Link"] = external_link if "instagram.com" not in external_link else ""
        except NoSuchElementException:
            print(f"  External link not found for {username}. (XPath might be outdated)")

        # Extract WhatsApp Number & Determine Region
        whatsapp_number, region = extract_whatsapp_number_and_region(bio_data["Bio"])
        bio_data["WhatsApp Number"] = whatsapp_number
        bio_data["Region"] = region

        print(f"✅ Scraped bio data for {username}: {bio_data}")

    except TimeoutException:
        print(f"❌ Timeout while loading page for {username}.")
    except Exception as e:
        print(f"❌ Error scraping bio for {username}: {e}")

    return bio_data

def scrape_bios(driver, usernames):
    """Scrapes bios for given usernames and returns structured data."""
    bios = []

    for username in usernames:
        bio_data = get_bio_data(driver, username)
        if bio_data:
            bios.append(bio_data)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    return bios
