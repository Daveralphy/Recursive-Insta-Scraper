import time
import random
import re # Needed for regex for WhatsApp extraction
import yaml
import pandas as pd # Although pandas is not directly used for scraping, it's common in these files
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Load configuration settings
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found in profile_scraper.py. Using default delays.")
    config = {"settings": {"delay_min": 5, "delay_max": 10}} # Fallback defaults

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

# Country code mapping for WhatsApp numbers (LATAM focus) - Brought from your old bio_scraper logic
COUNTRY_CODES = {
    "+1": "United States/Canada", "+44": "United Kingdom", "+234": "Nigeria",
    "+55": "Brazil", "+91": "India", "+52": "Mexico", "+54": "Argentina",
    "+56": "Chile", "+57": "Colombia", "+51": "Peru", "+593": "Ecuador",
    "+591": "Bolivia", "+598": "Uruguay", "+595": "Paraguay", "+502": "Guatemala",
    "+503": "El Salvador", "+504": "Honduras", "+505": "Nicaragua", "+506": "Costa Rica",
    "+507": "Panama", "+53": "Cuba", "+58": "Venezuela"
}

def extract_whatsapp_data(text_to_search):
    """
    Extracts a WhatsApp number (and potentially group link) and infers region from text.
    Combines logic for number and group link extraction.
    """
    whatsapp_number = ""
    whatsapp_group_link = ""
    region = ""

    # Regex for WhatsApp number (includes various formats, handles international codes)
    phone_pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,15}"
    # Regex for WhatsApp group links
    group_link_pattern = r"(?:https?://)?(?:chat\.)?whatsapp\.com/(?:invite/)?([a-zA-Z0-9]{22})"

    # 1. Extract WhatsApp Group Link
    group_link_match = re.search(group_link_pattern, text_to_search, re.IGNORECASE)
    if group_link_match:
        whatsapp_group_link = "https://chat.whatsapp.com/" + group_link_match.group(1)
        # If a group link is found, prioritize its presence
        print(f"    WhatsApp Group Link found: {whatsapp_group_link}")

    # 2. Extract WhatsApp Number
    # Search for a phone number that might be a WhatsApp number
    phone_match = re.search(phone_pattern, text_to_search)
    if phone_match:
        number = phone_match.group(0).strip()
        whatsapp_number = number
        print(f"    Potential WhatsApp Number found: {whatsapp_number}")

        # Try to infer region from the number's country code
        for code, country_name in COUNTRY_CODES.items():
            if number.startswith(code):
                region = country_name
                break
        else:
            # Fallback for region if country code not found but phone number exists
            if any(c in text_to_search.lower() for c in
                   ["latam", "latin america", "mexico", "colombia", "argentina", "chile", "peru", "brazil", "ecuador", "bolivia", "uruguay", "paraguay", "guatemala", "el salvador", "honduras", "nicaragua", "costa rica", "panama", "cuba", "venezuela"]):
                region = "LATAM (Inferred)"
            elif whatsapp_number: # If a number is found but no specific region, mark as general phone
                region = "Phone (Unknown Region)"
            else:
                region = "Unknown"

    # Final check for region if no number was found but city/country names are in bio
    if not region:
        for country_name in COUNTRY_CODES.values():
            if country_name.lower() in text_to_search.lower():
                region = country_name
                break
        if not region and any(city in text_to_search.lower() for city in ["bogota", "medellin", "santiago", "buenos aires", "lima", "quito", "la paz", "montevideo", "asuncion", "guatemala city", "san salvador", "tegucigalpa", "managua", "san jose", "panama city", "havana", "caracas", "mexico city", "sao paulo", "rio de janeiro"]):
            region = "LATAM (City Mention)"


    return whatsapp_number, whatsapp_group_link, region

def scrape_single_profile_details(driver, username):
    """
    Scrapes comprehensive data for a single Instagram profile using robust XPaths.
    Combines the best logic from your previous profile and bio scrapers.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"🔍 Scraping full details for profile: {username}")
    driver.get(profile_url)
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    profile_data = {
        "Username": username,
        "Full Name": "",
        "Follower Count": "0",
        "Following Count": "0",
        "Bio": "",
        "WhatsApp Number": "",
        "WhatsApp Group Link": "", # New field
        "Region": "",
        "External Link": "",
        "Profile URL": profile_url
    }

    try:
        wait = WebDriverWait(driver, 15)
        # Wait for the main header to be present
        wait.until(EC.presence_of_element_located((By.XPATH, "//header")))
        print(f"    Profile page for {username} loaded.")

        # --- Extract Full Name --- (Prioritize exact Full Name element, then fallback to bio)
        try:
            # XPath from your old get_profile_data for Full Name
            full_name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header/section/div[3]/div")))
            profile_data["Full Name"] = full_name_element.text.strip()
            print(f"    Full name extracted: {profile_data['Full Name']}")
        except (TimeoutException, NoSuchElementException):
            print(f"    Specific Full Name element not found for {username}.")

        # --- Extract Follower/Following Counts ---
        try:
            followers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers/')]/span/span")))
            profile_data["Follower Count"] = followers_element.text.replace(',', '').strip()
            print(f"    Follower count: {profile_data['Follower Count']}")
        except (TimeoutException, NoSuchElementException):
            print(f"    Follower count not found for {username}.")

        try:
            following_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following/')]/span/span")))
            profile_data["Following Count"] = following_element.text.replace(',', '').strip()
            print(f"    Following count: {profile_data['Following Count']}")
        except (TimeoutException, NoSuchElementException):
            print(f"    Following count not found for {username}.")

        # --- Extract Bio Text and Handle "more" button ---
        bio_text = ""
        try:
            # XPath from your old get_bio_data for the bio element
            bio_element_container = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x7a106z')]")))

            # Check for "...more" button & click it if present (from your old bio_scraper)
            try:
                more_button = bio_element_container.find_element(By.XPATH, ".//button[contains(text(), 'more')]")
                if more_button.is_displayed():
                    print(f"    Expanding full bio for {username}...")
                    more_button.click()
                    time.sleep(random.uniform(1, 2)) # Shorter sleep after click for bio expansion
            except NoSuchElementException:
                pass # No "...more" button found, continue normally

            bio_text = bio_element_container.text.strip()
            profile_data["Bio"] = bio_text
            print(f"    Bio extracted (full): {profile_data['Bio']}")

            # Fallback for Full Name: if not found by specific XPath, use first line of bio
            if not profile_data["Full Name"] and bio_text:
                bio_lines = bio_text.split("\n")
                if bio_lines:
                    profile_data["Full Name"] = bio_lines[0].strip()
                    print(f"    Using first line of bio as full name: {profile_data['Full Name']}")

        except (TimeoutException, NoSuchElementException):
            print(f"    Bio element not found for {username}. (XPath might be outdated or profile has no bio)")

        # --- Extract External Link ---
        try:
            # XPath from your old get_bio_data for external link - more general
            external_link_element = driver.find_element(By.XPATH, "//a[contains(@target, '_blank') and contains(@rel, 'nofollow')]")
            external_link = external_link_element.get_attribute("href")

            # Filter out Meta/Instagram links (from your old get_profile_data)
            if "meta.com" in external_link or "instagram.com" in external_link:
                profile_data["External Link"] = "" # Prevent storing Meta/Instagram links
                print(f"    Ignoring Meta/Instagram link: {external_link}")
            else:
                profile_data["External Link"] = external_link
                print(f"    External link found: {external_link}")
        except NoSuchElementException:
            print(f"    External link not found for {username}.")

        # --- Extract WhatsApp Number/Group Link & Determine Region ---
        # Search for WhatsApp data in both bio and external link
        combined_text_for_whatsapp = f"{profile_data['Bio']} {profile_data['External Link']}"
        whatsapp_num, whatsapp_group, region_inferred = extract_whatsapp_data(combined_text_for_whatsapp)
        profile_data["WhatsApp Number"] = whatsapp_num
        profile_data["WhatsApp Group Link"] = whatsapp_group
        profile_data["Region"] = region_inferred
        print(f"    WhatsApp: {whatsapp_num}, Group: {whatsapp_group}, Region: {region_inferred}")

        print(f"✅ Scraped all data for {username}: {profile_data}")

    except TimeoutException:
        print(f"❌ Timeout while loading page for {username}. Skipping.")
        return None # Return None if page doesn't load
    except Exception as e:
        print(f"❌ General error scraping {username}: {e}. Skipping.")
        return None # Return None on other scraping errors

    return profile_data

def scrape_profiles(driver, usernames):
    """
    Scrapes comprehensive profile data for a list of usernames.
    This is the main entry point from main.py for profile scraping.
    """
    profiles_data = []
    for username in usernames:
        data = scrape_single_profile_details(driver, username)
        if data:
            profiles_data.append(data)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    return profiles_data