import time
import random
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load configuration settings
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]

def get_profile_data(driver, username):
    """
    Extracts full name from the third line below followers/following counts.
    Ensures profile URL is correctly included in the exported data.
    Filters out Meta URLs.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"🔍 Scraping profile: {username}")
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))  

    profile_data = {
        "Username": username,
        "Full Name": "",
        "Follower Count": "0",
        "Following Count": "0",
        "Profile URL": profile_url,
        "External Link": ""  # Ensure external link filtering
    }

    try:
        wait = WebDriverWait(driver, 15)  
        wait.until(EC.presence_of_element_located((By.XPATH, "//header")))

        print(f"  Profile page for {username} loaded.")

        # Extract Full Name from the **third line, below followers/following counts**
        try:
            full_name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header/section/div[3]/div")))
            profile_data["Full Name"] = full_name_element.text.strip()
            print(f"  Full name extracted: {profile_data['Full Name']}")
        except (TimeoutException, NoSuchElementException):
            print(f"  Full name element not found for {username}, trying first line of bio instead.")

            # Fallback: Use First Line of Bio if Full Name Not Found
            try:
                bio_element = wait.until(EC.presence_of_element_located((By.XPATH, "//header/section/div/span")))
                bio_text = bio_element.text.strip()
                first_line = bio_text.split("\n")[0]  
                profile_data["Full Name"] = first_line  
                print(f"  Using first line of bio as full name: {first_line}")
            except:
                print(f"  Bio extraction failed for {username}. Full name not found.")

        # Extract Follower Count
        try:
            followers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers/')]/span/span")))
            profile_data["Follower Count"] = followers_element.text.replace(',', '').strip()
        except:
            print(f"  Follower count not found for {username}.")

        # Extract Following Count
        try:
            following_element = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following/')]/span/span")))
            profile_data["Following Count"] = following_element.text.replace(',', '').strip()
        except:
            print(f"  Following count not found for {username}.")

        # Extract External Link (Filter Out Meta URLs)
        try:
            external_link_element = driver.find_element(By.XPATH, "//header/section/div/a")
            external_link = external_link_element.get_attribute("href")

            if "meta.com" in external_link or "instagram.com" in external_link:
                profile_data["External Link"] = ""  # Prevent storing Meta/Instagram links
                print(f"  Ignoring Meta/Instagram link: {external_link}")
            else:
                profile_data["External Link"] = external_link  
                print(f"  External link found: {external_link}")
        except NoSuchElementException:
            print(f"  External link not found for {username}.")

        print(f"✅ Scraped data for {username}: {profile_data}")

    except TimeoutException:
        print(f"❌ Timeout while loading page for {username}.")
    except Exception as e:
        print(f"❌ Error scraping {username}: {e}")

    return profile_data

def scrape_profiles(driver, seed_usernames):
    """Scrapes profile data for given seed usernames."""
    profiles = []

    for username in seed_usernames:
        profile_data = get_profile_data(driver, username)
        if profile_data:
            profiles.append(profile_data)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  

    return profiles
