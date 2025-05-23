import time
import random
import yaml
import pandas as pd
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from profile_scraper import get_profile_data  # Import profile scraper to collect detailed profile info

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"]["follower_scrape_limit"]
KEYWORDS = ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"]  # Focus on phone retailers

def scroll_popup(driver):
    """Scrolls inside the followers or following pop-up window."""
    try:
        popup_window = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
        print("✅ Followers/Following pop-up detected!")

        for _ in range(10):  # Scroll multiple times to load more usernames
            driver.execute_script("arguments[0].scrollTop += 500;", popup_window)
            time.sleep(random.uniform(1, 3))  # Mimic human behavior

    except Exception as e:
        print(f"❌ Unable to locate followers/following pop-up: {e}")

def get_followers_from_popup(driver):
    """Extracts usernames from the followers or following pop-up."""
    usernames = set()

    try:
        follower_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]")))

        for element in follower_elements:
            href = element.get_attribute("href")
            if href:
                follower_username = href.split("/")[-2]
                usernames.add(follower_username)

        print(f"✅ Extracted {len(usernames)} usernames from pop-up")
        return list(usernames)

    except Exception as e:
        print(f"❌ Failed to extract usernames: {e}")
        return []

def scrape_followers_and_following(driver, seed_usernames):
    """Scrapes followers and following lists, filters relevant profiles, and extracts detailed profile data."""
    all_usernames = set()

    for username in seed_usernames:
        print(f"🔍 Visiting {username}'s profile...")

        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

        try:
            # Click Followers Button & Scrape
            followers_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]")))
            driver.execute_script("arguments[0].click();", followers_button)  # Ensures click works even if blocked
            time.sleep(5)  # Allow pop-up to load
            scroll_popup(driver)
            followers_list = get_followers_from_popup(driver)

            # Close followers pop-up
            try:
                close_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button")))
                close_button.click()
                time.sleep(3)
            except:
                print("⚠️ No close button found for followers pop-up.")

            # Click Following Button & Scrape
            following_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following/')]")))
            driver.execute_script("arguments[0].click();", following_button)  # Ensures click works even if blocked
            time.sleep(5)  # Allow pop-up to load
            scroll_popup(driver)
            following_list = get_followers_from_popup(driver)

            # Merge results and filter profiles
            potential_profiles = set(followers_list + following_list)
            print(f"🔎 Found {len(potential_profiles)} potential profiles.")

            for user in potential_profiles:
                profile_data = get_profile_data(driver, user)  # Calls profile scraper
                if any(keyword in profile_data["Bio"].lower() for keyword in KEYWORDS):
                    all_usernames.add(user)

        except Exception as e:
            print(f"❌ Error scraping {username}: {e}")

        if len(all_usernames) >= FOLLOWER_LIMIT:
            break

    print(f"✅ Scraping complete! {len(all_usernames)} relevant profiles collected.")
    return list(all_usernames)  # Returns filtered usernames for further scraping
