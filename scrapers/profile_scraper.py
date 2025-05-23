import time
import random
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load configuration settings
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

def get_profile_data(driver, username):
    """Extracts full name, username, followers count, following count, bio, and external link from an Instagram profile."""
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    try:
        print(f"🔍 Scraping profile: {username}")

        wait = WebDriverWait(driver, 10)

        # Extract Username from URL
        extracted_username = profile_url.split("/")[-2]

        # Extract Full Name (Word beside "Follow" button)
        try:
            full_name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header/section/div/h1")))
            full_name = full_name_element.text.strip() if full_name_element else ""
        except:
            full_name = ""

        # Extract Follower Count (Number before "followers")
        try:
            followers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//ul/li[2]/a/span")))
            followers_count = followers_element.text.strip() if followers_element else "0"
        except:
            followers_count = "0"

        # Extract Following Count (Number before "following")
        try:
            following_element = wait.until(EC.presence_of_element_located((By.XPATH, "//ul/li[3]/a/span")))
            following_count = following_element.text.strip() if following_element else "0"
        except:
            following_count = "0"

        # Extract Bio Text (Below full name)
        try:
            bio_element = driver.find_elements(By.XPATH, "//header/section/div/span")
            bio_text = bio_element[0].text.strip() if bio_element else ""
        except:
            bio_text = ""

        # Extract External Link (If available)
        try:
            external_link_element = driver.find_elements(By.XPATH, "//header/section/div/a")
            external_link = external_link_element[0].get_attribute("href") if external_link_element else ""
        except:
            external_link = ""

        return {
            "Username": extracted_username,
            "Full Name": full_name,
            "Follower Count": followers_count,
            "Following Count": following_count,
            "Bio": bio_text,
            "External Link": external_link if "instagram.com" not in external_link else "",  # Prevent profile URL from being saved as external link
            "Profile URL": profile_url
        }
    except Exception as e:
        print(f"❌ Failed to scrape profile: {username} -> {e}")
        return {}

def scrape_profiles(driver, seed_usernames):
    """Scrapes profile data for given seed usernames and returns structured data."""
    profiles = []

    for username in seed_usernames:
        profile_data = get_profile_data(driver, username)
        if profile_data:
            profiles.append(profile_data)

    return profiles  # Returns extracted profile details for further use
