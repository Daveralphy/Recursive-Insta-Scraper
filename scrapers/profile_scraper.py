import time
import random
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Load configuration settings
# Assuming config.yaml is in the root directory accessible from where main.py runs
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

def get_profile_data(driver, username):
    """
    Extracts full name, username, followers count, and following count
    from an Instagram profile using a pre-logged-in WebDriver instance.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"🔍 Scraping profile: {username}")
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX)) # Add delay after navigating to profile

    profile_data = {
        "Username": username,
        "Full Name": "",
        "Follower Count": "0", # Default value, will be overwritten if found
        "Following Count": "0", # Default value, will be overwritten if found
        "Profile URL": profile_url
    }

    try:
        # Wait for the main profile header to load, indicating the page content is ready
        wait = WebDriverWait(driver, 15) # Increased wait time for robustness
        wait.until(EC.presence_of_element_located((By.XPATH, "//header//h2")))
        print(f"  Profile page for {username} loaded.")

        # Extract Full Name
        try:
            # Common XPath for the element containing the full name (often an h2 with specific classes)
            # This XPath targets a text element that is typically the full name on the profile.
            full_name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(@class, 'x1lli2ws') and contains(@class, 'x1n2onr6') and contains(@class, 'xhnbmfe')]")))
            profile_data["Full Name"] = full_name_element.text.strip()
        except TimeoutException:
            print(f"  Full name element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Full name not found for {username}. (XPath might be outdated)")


        # Extract Follower Count
        try:
            # Look for the <a> tag with an href containing '/followers/' and get the count from its child span.
            # The count itself is often in a 'title' attribute or as text.
            followers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers/')]/span/span")))
            followers_count_text = followers_element.get_attribute("title") or followers_element.text
            profile_data["Follower Count"] = followers_count_text.replace(',', '').strip() # Remove commas for clean numbers
        except TimeoutException:
            print(f"  Follower count element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Follower count not found for {username}. (XPath might be outdated)")

        # Extract Following Count
        try:
            # Similar to followers, but looking for '/following/'.
            following_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following/')]/span/span")))
            following_count_text = following_element.get_attribute("title") or following_element.text
            profile_data["Following Count"] = following_count_text.replace(',', '').strip() # Remove commas for clean numbers
        except TimeoutException:
            print(f"  Following count element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Following count not found for {username}. (XPath might be outdated)")

        print(f"✅ Scraped data for {username}:")
        for key, value in profile_data.items():
            print(f"    {key}: {value}")

    except TimeoutException:
        print(f"❌ Timeout while loading page for {username}. This often means the page did not load completely within the given time, or the initial selectors are incorrect.")
        print("  Current page source for debugging (first 2000 chars):")
        print(driver.page_source[:2000]) # Print first 2000 characters of page source for debugging
    except Exception as e:
        print(f"❌ An unexpected error occurred while scraping {username}: {e}")

    return profile_data

def scrape_profiles(driver, seed_usernames):
    """Scrapes profile data for given seed usernames and returns structured data."""
    profiles = []

    for username in seed_usernames:
        profile_data = get_profile_data(driver, username)
        if profile_data:
            profiles.append(profile_data)
        # Introduce a random delay between requests to avoid rate limiting
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    return profiles