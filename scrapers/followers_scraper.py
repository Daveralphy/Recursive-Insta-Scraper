import time
import random
import yaml
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"]["follower_scrape_limit"]
SEED_USERNAMES = config["seed_usernames"]
KEYWORDS = ["celulares", "accesorios", "mayorista", "distribuidor"]  # Keywords for filtering retail sellers

def get_followers(driver, username):
    """Visits a profile, clicks 'Followers', scrolls inside the pop-up, and scrapes follower usernames."""
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

    followers = set()

    try:
        print(f"🔍 Visiting {username}'s profile...")

        # Wait for the "Followers" button and click it
        wait = WebDriverWait(driver, 10)
        followers_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]")))
        followers_button.click()
        time.sleep(5)  # Allow pop-up to load

        print("📜 Followers pop-up opened, scrolling & scraping usernames...")

        # Locate followers pop-up window
        followers_list = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']/div/div")))

        # Scroll inside the pop-up dynamically
        for _ in range(15):  # Adjust scroll depth as needed
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", followers_list)
            time.sleep(random.uniform(2, 4))

            follower_elements = driver.find_elements(By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]")
            for element in follower_elements:
                href = element.get_attribute("href")
                if href:
                    follower_username = href.split("/")[-2]

                    # Scrape only if follower bio matches keywords
                    bio_text = element.get_attribute("innerText").lower()
                    if any(keyword in bio_text for keyword in KEYWORDS):
                        followers.add(follower_username)

            if len(followers) >= FOLLOWER_LIMIT:
                break

        print(f"✅ Collected {len(followers)} filtered followers from {username}")
        return list(followers)

    except Exception as e:
        print(f"❌ Failed to scrape followers for {username}: {e}")
        return []

def scrape_followers(driver):
    """Scrapes followers for seed usernames from the config file."""
    all_followers = set()

    for username in SEED_USERNAMES:
        followers = get_followers(driver, username)
        all_followers.update(followers)

        if len(all_followers) >= FOLLOWER_LIMIT:
            break

    # Save results to CSV
    df = pd.DataFrame({"Username": list(all_followers)})
    df.to_csv("data/instagram_followers.csv", index=False)
    print(f"✅ Scraping complete! {len(all_followers)} followers saved to data/instagram_followers.csv")

    return list(all_followers)  # Returns newly collected followers for next scraper
