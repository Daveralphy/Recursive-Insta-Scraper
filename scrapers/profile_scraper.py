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
    "1": "USA/Canada", "44": "United Kingdom", "234": "Nigeria",
    "55": "Brazil", "91": "India", "52": "Mexico", "54": "Argentina",
    "56": "Chile", "57": "Colombia", "51": "Peru", "593": "Ecuador",
    "591": "Bolivia", "598": "Uruguay", "595": "Paraguay", "502": "Guatemala",
    "503": "El Salvador", "504": "Honduras", "505": "Nicaragua", "506": "Costa Rica",
    "507": "Panama", "53": "Cuba", "58": "Venezuela"
}

def extract_whatsapp_data(text_to_search, default_country_code=None):
    """
    Extracts a WhatsApp number (and potentially group link) and infers region from text.
    Combines logic for number, wa.me links, api.whatsapp.com links, and group link extraction,
    with number normalization directly integrated.
    Prioritizes direct links for numbers.

    Args:
        text_to_search (str): The text (e.g., bio, external link) to search for WhatsApp data.
        default_country_code (str, optional): A default country code (e.g., "+234") to use
                                             for normalizing local numbers without explicit codes.

    Returns:
        tuple: (normalized_whatsapp_number, whatsapp_group_link, region)
    """
    whatsapp_number = ""  # Stores the raw/less-processed extracted number
    normalized_whatsapp_number = ""  # Stores the number in E.164 format (+CCNNNNNNNNN)
    whatsapp_group_link = ""
    region = ""

    # Helper for inline number normalization
    def _normalize_number_inline(num_str):
        if not num_str:
            return ""

        # Remove all non-digit characters, except for a leading '+'
        cleaned_num = re.sub(r'[^\d+]', '', num_str)

        # If it already starts with '+', it's likely already in or close to E.164
        if cleaned_num.startswith("+"):
            return cleaned_num

        # If it starts with '00', replace with '+' (common international dial-out prefix)
        if cleaned_num.startswith("00") and len(cleaned_num) > 2:
            return "+" + cleaned_num[2:]

        # If it starts with '0' (common for local dialing, e.g., in Nigeria 080...)
        # and we have a default country code, try to normalize.
        # The default_country_code should include the '+' (e.g., "+234").
        if cleaned_num.startswith("0") and default_country_code and len(cleaned_num) > 1:
            return default_country_code + cleaned_num[1:]

        # If no '+' and no '00' prefix, try to match against known country codes
        # This loop checks if the number starts with a known country code (e.g., "234" for Nigeria)
        for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):  # Check longer codes first
            if cleaned_num.startswith(code) and len(cleaned_num) > len(code):
                return "+" + cleaned_num

        # Fallback: if no international prefix, and no default country code,
        # or no country code match, just return as is (digits only).
        # It will not be fully E.164 unless a country code can be inferred later.
        return cleaned_num

    # Regex patterns
    group_link_pattern = r"(?:https?://)?(?:chat\.)?whatsapp\.com/(?:invite/)?([a-zA-Z0-9]{22})"
    wa_me_pattern = r"(?:https?://)?wa\.me/(\d+)"
    api_whatsapp_pattern = r"(?:https?://)?api\.whatsapp\.com/send\?phone=(\d+)"
    phone_pattern = r"((?:\+\d{1,4}[-.\s]?)?(?:\(?\d{2,5}\)?[-.\s]?){1,2}\d{3,4}[-.\s]?\d{3,4})"


    # 1. Extract WhatsApp Group Link (independent, doesn't affect number extraction)
    group_link_match = re.search(group_link_pattern, text_to_search, re.IGNORECASE)
    if group_link_match:
        whatsapp_group_link = "https://chat.whatsapp.com/" + group_link_match.group(1)
        print(f"    WhatsApp Group Link found: {whatsapp_group_link}")

    # 2. Extract WhatsApp Number from direct links (wa.me or api.whatsapp.com/send?phone=) - highest priority
    # Try wa.me first
    wa_me_match = re.search(wa_me_pattern, text_to_search, re.IGNORECASE)
    if wa_me_match:
        potential_number = wa_me_match.group(1)
        normalized_whatsapp_number = _normalize_number_inline(potential_number)
        whatsapp_number = potential_number # Store original for logging if desired
        print(f"    WhatsApp number from wa.me link: {normalized_whatsapp_number}")
    else:
        # If no wa.me, try api.whatsapp.com/send?phone=
        api_whatsapp_match = re.search(api_whatsapp_pattern, text_to_search, re.IGNORECASE)
        if api_whatsapp_match:
            potential_number = api_whatsapp_match.group(1)
            normalized_whatsapp_number = _normalize_number_inline(potential_number)
            whatsapp_number = potential_number # Store original
            print(f"    WhatsApp number from api.whatsapp.com link: {normalized_whatsapp_number}")

    # 3. Extract WhatsApp Number from general text if not already found via direct links
    if not normalized_whatsapp_number: # Only search for raw number if not already extracted
        phone_match = re.search(phone_pattern, text_to_search)
        if phone_match:
            raw_number = phone_match.group(1).strip()
            whatsapp_number = raw_number # Store the raw number found
            
            # Use the inline normalization helper for this raw number
            normalized_whatsapp_number = _normalize_number_inline(raw_number)

            print(f"    Potential WhatsApp Number found from text: {whatsapp_number}")
            if normalized_whatsapp_number and normalized_whatsapp_number != whatsapp_number:
                print(f"    Normalized WhatsApp Number: {normalized_whatsapp_number}")
            elif not normalized_whatsapp_number:
                print(f"    Warning: Number '{whatsapp_number}' could not be normalized.")


    # 4. Infer Region (using normalized number if available, then raw number, then text)
    region = "Unknown" # Default to unknown if no specific match

    # Prioritize region inference from the normalized number's country code
    if normalized_whatsapp_number and normalized_whatsapp_number.startswith('+'):
        # Check against COUNTRY_CODES keys, which are expected to be digits only (e.g., "234")
        for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True): # Check longer codes first
            if normalized_whatsapp_number.startswith("+" + code): # Add '+' for comparison with normalized number
                region = COUNTRY_CODES[code]
                break

    # If no region from number, try from text clues (e.g., cities, country names in bio)
    if region == "Unknown":
        text_lower = text_to_search.lower()
        
        # Check for explicit country names in text
        found_country_by_name = False
        for country_code, country_name in COUNTRY_CODES.items():
            if country_name.lower() in text_lower:
                region = country_name + " (Bio Mention)"
                found_country_by_name = True
                break
        
        if not found_country_by_name: # Only check cities if no country name was found
            # Broad list of LATAM and African cities
            if any(city in text_lower for city in ["bogota", "medellin", "santiago", "buenos aires", "lima", "quito", "la paz", "montevideo", "asuncion", "guatemala city", "san salvador", "tegucigalpa", "managua", "san jose", "panama city", "havana", "caracas", "mexico city", "sao paulo", "rio de janeiro", "lagos", "abuja", "nairobi", "johannesburg"]):
                region = "LATAM/Africa (City Mention)"
            elif normalized_whatsapp_number: # If a number is found but no specific region, mark as general phone
                region = "Phone (Unknown Region)"


    return normalized_whatsapp_number, whatsapp_group_link, region

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

            full_bio_text = bio_element_container.text.strip()
            
            # Split bio into lines
            bio_lines = full_bio_text.split('\n')
            
            # The first line has already been stripped for Full Name.
            # Now, construct the 'Bio' field by joining lines from the third line onwards.
            # If there's only one line, that's the bio.
            # If there are two lines, the second line is stripped out, so the bio is just the first line.
            if len(bio_lines) > 2:
                # If there are more than 2 lines, join from the 3rd line onwards
                profile_data["Bio"] = "\n".join(bio_lines[2:]).strip()
            elif len(bio_lines) == 2:
                # If there are exactly two lines, the second line is stripped out, so bio is empty or implied to be only the first line (already handled by Full Name fallback).
                # To be clear, we'll make it empty if the second line is the last relevant part.
                profile_data["Bio"] = "" 
            elif len(bio_lines) == 1:
                # If there's only one line, it's used for Full Name fallback, and the bio would technically be that line.
                # However, if Full Name is already populated, and we want to strip the second line, this means
                # if there's only one line, it's likely already consumed by Full Name.
                # If it wasn't consumed by Full Name (e.g., Full Name was found by XPath), then the single line
                # would be the entire bio. Let's make sure it's not duplicated.
                # Since Full Name fallback will take the first line if bio_text exists and Full Name is empty,
                # we should only populate 'Bio' with the first line if it's the *only* line and Full Name *wasn't* already taken from it.
                # Given your instruction, if the first line populates Full Name, and the second is stripped,
                # then if there's only one line, after potentially populating Full Name, the 'Bio' field should reflect the *remaining* bio content.
                # The prompt implies we want to remove the first *and* second line from the bio field if they exist.
                # So, if only one line exists, and it goes to Full Name, then Bio is empty.
                profile_data["Bio"] = "" # If only one line, it's typically full name or very short.
            
            print(f"    Bio extracted (after stripping first two lines if applicable): {profile_data['Bio']}")

            # Fallback for Full Name: if not found by specific XPath, use first line of full_bio_text
            # This logic should happen *before* modifying profile_data["Bio"]
            if not profile_data["Full Name"] and bio_lines:
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
        # Search for WhatsApp data in both bio (which now excludes the first two lines) and external link.
        # We need to include the second line *here* for WhatsApp search, even if it's stripped from the 'Bio' field.
        # So we'll use the original full_bio_text for WhatsApp extraction.
        combined_text_for_whatsapp = f"{full_bio_text if 'full_bio_text' in locals() else ''} {profile_data['External Link']}"
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