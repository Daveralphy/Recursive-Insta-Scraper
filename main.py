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

from scrapers.profile_scraper import scrape_profiles # This now returns list of dicts {Username: ..., Full Name: ..., ...}
from scrapers.bio_scraper import scrape_bios         # This now returns list of dicts {Username: ..., Bio: ..., ...}
from scrapers.followers_scraper import scrape_followers_and_following # This returns only a list of usernames

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
    exit("Configuration file missing.") # Exit if config is essential

VISIBLE_BROWSER = config["settings"]["visible_browser"]
SEED_USERNAMES = config["seed_usernames"]

# Define a default list of user agents if not provided or empty in config.yaml
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/108.0.1462.54",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/108.0",
]

# Initialize Selenium WebDriver
try:
    print("🚀 Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    if not VISIBLE_BROWSER:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Get user agents from config, or use default if not present or empty
    user_agents_list = config.get('user_agents', DEFAULT_USER_AGENTS)
    if not user_agents_list: # Ensure it's not empty even if config provides an empty list
        user_agents_list = DEFAULT_USER_AGENTS
        print("⚠️ 'user_agents' list in config.yaml is empty or missing. Using default user agents.")

    options.add_argument(f"user-agent={random.choice(user_agents_list)}")
    options.add_argument("--window-size=1920,1080") # Ensure consistent window size

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
    # Wait for username and password fields to be present
    username_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_field = driver.find_element(By.NAME, "password")

    username_field.send_keys(INSTAGRAM_USERNAME)
    password_field.send_keys(INSTAGRAM_PASSWORD)
    password_field.send_keys(Keys.RETURN)

    time.sleep(random.randint(5, 10))  # Wait for login to process
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
    # Wait for a potential 2FA input field or the home page to load
    WebDriverWait(driver, 15).until(
        EC.any_of(
            EC.presence_of_element_located((By.NAME, "verificationCode")), # 2FA code input
            EC.url_contains("instagram.com") # Check if already on home page
        )
    )

    security_code_inputs = driver.find_elements(By.NAME, "verificationCode")

    if security_code_inputs:
        print("⚠️ Instagram requires Two-Factor Authentication (2FA).")
        security_code = input("🔐 Enter the 2FA code sent to your device: ")

        if security_code:
            security_code_inputs[0].send_keys(security_code)
            # Find the submit button for 2FA, often a button with specific text or role
            try:
                verify_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Confirm'] | //button[text()='Verify'] | //button[text()='Next']"))
                )
                verify_button.click()
                print("✅ Two-factor authentication submitted! Waiting for confirmation...")
                WebDriverWait(driver, 20).until(EC.url_contains("instagram.com")) # Wait for successful 2FA
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
        # Wait for "Not Now" button in a dialog
        not_now_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button[text()='Not Now']"))
        )
        not_now_button.click()
        print("Clicked 'Not Now' on pop-up.")
        time.sleep(random.uniform(1, 2))
    except TimeoutException:
        pass # No pop-up found or it disappeared quickly
    except Exception as e:
        print(f"Error handling post-login pop-up: {e}")

except Exception as e:
    print(f"⚠️ An error occurred during 2FA check/handling: {e}")

# Final login confirmation
try:
    time.sleep(5) # Allow Instagram to fully load after login/2FA
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

# --- Start comprehensive scraping process ---
all_profiles_data = []
all_bios_data = []
processed_usernames = set() # Keep track of usernames for which we've already scraped full data

# 1. Scrape initial seed usernames for profile and bio data
print("\n🚀 Scraping initial seed usernames for full profile and bio data...")
for username in SEED_USERNAMES:
    if username not in processed_usernames:
        profile_data = scrape_profiles(driver, [username]) # scrape_profiles expects a list
        if profile_data:
            all_profiles_data.extend(profile_data)
        
        bio_data = scrape_bios(driver, [username]) # scrape_bios expects a list
        if bio_data:
            all_bios_data.extend(bio_data)
        
        processed_usernames.add(username)
        time.sleep(random.uniform(config["settings"]["delay_min"], config["settings"]["delay_max"])) # Delay between profiles

# 2. Expand search for new relevant profiles using followers_scraper
print("\n🚀 Expanding search for new relevant profiles using followers/following...")
new_usernames = scrape_followers_and_following(driver, SEED_USERNAMES)
print(f"📂 Total new relevant usernames found: {len(new_usernames)}")

# 3. Scrape full profile and bio data for newly found usernames (if not already processed)
print("\n🚀 Collecting full data for newly found relevant profiles...")
for username in new_usernames:
    if username not in processed_usernames:
        print(f"  Scraping full data for new profile: {username}...")
        profile_data = scrape_profiles(driver, [username])
        if profile_data:
            all_profiles_data.extend(profile_data)
        
        bio_data = scrape_bios(driver, [username])
        if bio_data:
            all_bios_data.extend(bio_data)
        
        processed_usernames.add(username)
        time.sleep(random.uniform(config["settings"]["delay_min"], config["settings"]["delay_max"])) # Delay between new profiles

# Close browser session after all scraping is done
driver.quit()
print("\n✅ Scraping process completed successfully!")

# --- Data Merging and Saving ---
# Convert lists of dicts to DataFrames
df_profiles = pd.DataFrame(all_profiles_data)
df_bios = pd.DataFrame(all_bios_data)

# Remove potential duplicates based on 'Username' before merging
# This handles cases where a username might have been processed multiple times
df_profiles_unique = df_profiles.drop_duplicates(subset=['Username']).set_index('Username')
df_bios_unique = df_bios.drop_duplicates(subset=['Username']).set_index('Username')

# Merge profiles and bios data
final_df = df_profiles_unique.merge(df_bios_unique, on="Username", how="outer", suffixes=('_profile', '_bio'))

# Reset index to make 'Username' a column again
final_df = final_df.reset_index()

# Reorder columns to match desired output (optional, but good for consistency)
desired_columns_order = [
    "Username",
    "Full Name",
    "Follower Count",
    "Following Count",
    "Bio",
    "WhatsApp Number",
    "Region",
    "External Link",
    "Profile URL"
]
# Ensure all desired columns exist, fill missing ones with empty string/NaN
for col in desired_columns_order:
    if col not in final_df.columns:
        final_df[col] = '' # Or pd.NA or np.nan

final_df = final_df[desired_columns_order]

# Save final combined data to CSV
output_dir = "data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_path = os.path.join(output_dir, "instagram_scraped_data.csv")
final_df.to_csv(output_path, index=False)

print(f"✅ Final data saved to {output_path}")
