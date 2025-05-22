import time
import random
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
SEED_USERNAMES = config["seed_usernames"]

def get_profile_data(driver, username):
    """Extracts full name, username, and follower count from an Instagram profile."""
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    try:
        print(f"🔍 Scraping profile for {username}...")

        wait = WebDriverWait(driver, 10)

        # Extract full name (return blank if not found)
        try:
            full_name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header//section//h2")))
            full_name = full_name_element.text if full_name_element else ""
        except:
            full_name = ""

        # Extract follower count (return blank if not found)
        try:
            followers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header//section//ul/li[2]//span")))
            followers_count = followers_element.text if followers_element else ""
        except:
            followers_count = ""

        # If both are blank, assume the page does not exist
        if not full_name and not followers_count:
            print(f"⚠️ No profile data found for {username}. Returning blank values.")
            return {}

        return {
            "Username": username,
            "Full Name": full_name,
            "Follower Count": followers_count,
            "Profile URL": profile_url
        }
    except Exception as e:
        print(f"❌ Failed to scrape profile for {username}: {e}")
        return {}

def scrape_profiles(driver, followers):
    """Scrapes profile data for usernames collected from followers."""
    profiles = []

    for username in followers:
        profile_data = get_profile_data(driver, username)
        if profile_data:
            profiles.append(profile_data)

    # Save to CSV
    df = pd.DataFrame(profiles)
    df.to_csv("data/instagram_profiles.csv", index=False)
    print(f"✅ Profile scraping complete! {len(profiles)} profiles saved to data/instagram_profiles.csv")
