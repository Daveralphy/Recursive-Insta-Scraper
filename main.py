import os
import time
import random
import yaml
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Ensure correct import paths for scraper modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scrapers')))

from scrapers.profile_scraper import scrape_profiles
from scrapers.followers_scraper import scrape_followers_and_following
from scrapers.classifier import classify_profile
from exporter import export_data_live

# Load environment variables (credentials)
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Load config settings
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    exit("Configuration file missing.")

VISIBLE_BROWSER = config["settings"]["visible_browser"]
SEED_USERNAMES = config["seed_usernames"]

user_agents_list = config.get('user_agents')

if not user_agents_list:
    print("❌ Error: 'user_agents' list is missing or empty in config.yaml.")
    print("Please ensure you have a 'user_agents' section with at least one user agent defined in config.yaml.")
    exit("User agents configuration missing.")
elif not isinstance(user_agents_list, list):
    print("❌ Error: 'user_agents' in config.yaml must be a list.")
    exit("Invalid user agents configuration.")


# Initialize Selenium WebDriver
try:
    print("🚀 Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    if not VISIBLE_BROWSER:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    options.add_argument(f"user-agent={random.choice(user_agents_list)}")
    options.add_argument("--window-size=1920,1080") # Ensure consistent window size

    driver_path = ChromeDriverManager().install()
    print(f"Using ChromeDriver from: {driver_path}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("✅ Chrome WebDriver launched successfully!")
except Exception as e:
    print(f"❌ WebDriver initialization failed: {e}")
    exit()

# Open Instagram login page
print("🔍 Opening Instagram login page...")
driver.get("https://www.instagram.com/accounts/login/")
time.sleep(random.randint(5, 10))

# Enter login credentials
try:
    print("🔑 Entering login credentials...")
    username_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_field = driver.find_element(By.NAME, "password")

    username_field.send_keys(INSTAGRAM_USERNAME)
    password_field.send_keys(INSTAGRAM_PASSWORD)
    password_field.send_keys(Keys.RETURN)

    time.sleep(random.randint(5, 10))
    print("✅ Login details entered successfully!")
except TimeoutException:
    print("❌ Login failed: Username/password fields or login button not found within timeout.")
    print("Current page source for debugging login issue:")
    print(driver.page_source[:2000])
    driver.quit()
    exit()
except NoSuchElementException as e:
    print(f"❌ Login failed: Element not found - {e}")
    driver.quit()
    exit()
except Exception as e:
    print(f"❌ Failed to enter login credentials: {e}")
    driver.quit()
    exit()

# Detect and handle Two-Factor Authentication (2FA)
try:
    print("🔍 Checking for 2FA prompt...")
    WebDriverWait(driver, 15).until(
        EC.any_of(
            EC.presence_of_element_located((By.NAME, "verificationCode")),
            EC.url_contains("instagram.com")
        )
    )

    security_code_inputs = driver.find_elements(By.NAME, "verificationCode")

    if security_code_inputs:
        print("⚠️ Instagram requires Two-Factor Authentication (2FA).")
        security_code = input("🔐 Enter the 2FA code sent to your device: ")

        if security_code:
            security_code_inputs[0].send_keys(security_code)
            try:
                verify_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Confirm'] | //button[text()='Verify'] | //button[text()='Next']"))
                )
                verify_button.click()
                print("✅ Two-factor authentication submitted! Waiting for confirmation...")
                WebDriverWait(driver, 20).until(EC.url_contains("instagram.com"))
                print("✅ 2FA authentication successful!")
            except TimeoutException:
                print("❌ 2FA verification button not found or 2FA failed to confirm within timeout.")
                driver.quit()
                exit()
            except Exception as e:
                print(f"❌ Error submitting 2FA: {e}")
                driver.quit()
                exit()
        else:
            print("❌ No 2FA code entered, exiting.")
            driver.quit()
            exit()
    else:
        print("✅ No 2FA challenge detected or already passed.")

    # Handle post-login pop-ups (Save Info, Turn on Notifications)
    try:
        not_now_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button[text()='Not Now']"))
        )
        not_now_button.click()
        print("Clicked 'Not Now' on pop-up.")
        time.sleep(random.uniform(1, 2))
    except TimeoutException:
        pass
    except Exception as e:
        print(f"Error handling post-login pop-up: {e}")

except Exception as e:
    print(f"⚠️ An error occurred during 2FA check/handling: {e}")

# Final login confirmation
try:
    time.sleep(5)
    current_url = driver.current_url
    print(f"🔗 Current URL after login confirmation: {current_url}")

    if "accounts/login" in current_url or "challenge" in current_url:
        print("❌ Login failed! Verify credentials or complete security checks.")
        driver.quit()
        exit()
    print("✅ Login successful and confirmed!")
except Exception as e:
    print(f"❌ Unexpected login confirmation failure: {e}")
    driver.quit()
    exit()

## **Start Comprehensive Scraping Process with Live Export**
# Use a set to track usernames that have been processed and exported
# This prevents re-processing and re-exporting the same profile multiple times.
processed_usernames_for_export = set()

# Helper function to classify and live export a single profile
def process_and_live_export_profile(profile_data_item, config, processed_usernames_set):
    """
    Classifies a single profile dictionary and immediately sends it to the live exporter.
    Prevents re-processing and re-exporting the same username if already handled.

    Args:
        profile_data_item (dict): A dictionary containing scraped profile data.
        config (dict): The loaded configuration dictionary.
        processed_usernames_set (set): A set to track usernames already processed and exported.
    """
    username = profile_data_item.get("Username")
    if not username:
        print("⚠️ Skipping profile with no Username for live export.")
        return

    if username in processed_usernames_set:
        # print(f"    Skipping already processed and exported user: {username}") # Uncomment for debugging
        return

    print(f"    Classifying and preparing for live export: {username}...")
    
    # Classify the profile. This function modifies `profile_data_item` in place,
    # adding 'Classification', cleaning 'Bio', and extracting other details.
    classify_profile(profile_data_item) 
    
    # Export this single classified profile.
    # export_data_live expects a list of dictionaries, so we pass a list with one item.
    export_data_live([profile_data_item], config) 

    # Add username to the set of processed profiles to avoid future duplicates
    processed_usernames_set.add(username)


# --- Step 1: Process Seed Instagram Usernames ---
print("\n🚀 Step 1: Scraping and live exporting initial seed usernames...")
for username in SEED_USERNAMES:
    if username not in processed_usernames_for_export: # Check before even scraping if already processed
        print(f"    Scraping full data for seed profile: {username}...")
        profile_data_list = scrape_profiles(driver, [username])

        if profile_data_list:
            for profile in profile_data_list:
                process_and_live_export_profile(profile, config, processed_usernames_for_export)
        else:
            print(f"    No full profile data collected for seed {username}.")
        
        # Introduce a delay to avoid bot detection
        time.sleep(random.uniform(config["settings"]["delay_min"], config["settings"]["delay_max"]))


# --- Step 2 & 3: Expand search for new relevant profiles with live export ---
print("\n🚀 Step 2 & 3: Expanding search for new relevant profiles using followers/following and filtering (Live Export)...")

# scrape_followers_and_following now handles the full scrape and live export internally
scrape_followers_and_following(
    driver,
    list(processed_usernames_for_export), # Start expansion from already processed (seed) users
    process_and_live_export_profile, # Pass the live export function
    scrape_profiles, # Pass the full profile scraper function
    config, # Pass config
    current_depth=0, # Start recursion depth at 0
    scraped_usernames_set=processed_usernames_for_export # Pass the master set for tracking
)

# No need for Step 4 explicitly in main.py, as it's now handled by followers_scraper.py itself.

# Close browser session after all scraping is done
driver.quit()
print("\n✅ Scraping and live export process completed successfully!")

# The large final data processing and export block is no longer needed here
# because data is exported as it's processed live.

print(f"Summary: Total unique profiles processed and exported: {len(processed_usernames_for_export)}")