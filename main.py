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
# from scrapers.bio_scraper import scrape_bios # REMOVED: profile_scraper handles Bio and Full Name
from scrapers.followers_scraper import scrape_followers_and_following # This returns only a list of usernames
from scrapers.classifier import classify_profile # NEW: For Step 5 AI Classification

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
final_scraped_data = [] # Stores all comprehensive profile data
all_processed_usernames = set() # Tracks all usernames for which a full scrape has been done

# Step 1: Input Seed Instagram Usernames (implicitly handled by SEED_USERNAMES)
# Initial full scrape for seed usernames, as they are key relevant profiles
print("\n🚀 Step 1 & 4 (Partial): Scraping initial seed usernames for full profile data...")
for username in SEED_USERNAMES:
    if username not in all_processed_usernames:
        print(f"    Scraping full data for seed profile: {username}...")
        profile_data_list = scrape_profiles(driver, [username]) # scrape_profiles expects a list

        if profile_data_list:
            final_scraped_data.extend(profile_data_list)
            for profile in profile_data_list: # Add each scraped username to the set
                all_processed_usernames.add(profile.get("Username"))
        else:
            print(f"    No full profile data collected for seed {username}.")
        
        time.sleep(random.uniform(config["settings"]["delay_min"], config["settings"]["delay_max"]))


# Step 2 & 3: Expand search for new relevant profiles using followers_scraper & Light Scrape for AI Filtering
# The scrape_followers_and_following function now performs the light scrape and filtering internally
print("\n🚀 Step 2 & 3: Expanding search for new relevant profiles using followers/following and filtering...")
# The third argument 'scrape_profiles' is implicitly used by followers_scraper for its light scrape
relevant_usernames_from_expansion = scrape_followers_and_following(driver, list(all_processed_usernames), scrape_profiles)
print(f"📂 Total new relevant usernames found from expansion and filtering: {len(relevant_usernames_from_expansion)}")

# Consolidate all usernames that need a full scrape (seeds already scraped, new ones need it)
# We only want to scrape profiles that haven't been processed yet
usernames_for_full_scrape_after_expansion = [
    username for username in relevant_usernames_from_expansion 
    if username not in all_processed_usernames
]

print(f"\nTotal unique new usernames to perform full scrape on after initial expansion: {len(usernames_for_full_scrape_after_expansion)}")


# Step 4: Full Profile Scrape (Continued - for newly found and filtered usernames)
print("\n🚀 Step 4 (Continued): Performing full profile scrape for newly found relevant accounts...")
for username in usernames_for_full_scrape_after_expansion:
    print(f"    Collecting full data for new relevant profile: {username}...")
    profile_data_list = scrape_profiles(driver, [username])

    if profile_data_list:
        final_scraped_data.extend(profile_data_list)
        for profile in profile_data_list: # Ensure each scraped username is added to the set
            all_processed_usernames.add(profile.get("Username"))
    else:
        print(f"    No full profile data collected for new relevant {username}.")

    time.sleep(random.uniform(config["settings"]["delay_min"], config["settings"]["delay_max"]))

# Close browser session after all scraping is done
driver.quit()
print("\n✅ Scraping process completed successfully!")

# --- Data Processing and Saving ---

# Step 5: AI Classification
print("\n🚀 Step 5: Classifying all collected profiles...")
# Iterate through final_scraped_data to add classification
for profile in final_scraped_data:
    classification = classify_profile(profile) # Call the classifier function
    profile["Classification"] = classification
    # print(f"    Classified {profile.get('Username')}: {profile.get('Classification')}") # Optional for detailed logging


# Step 6: Save Results
print("\n🚀 Step 6: Preparing and saving final data...")

# Create DataFrame from collected data
# Ensure unique profiles by converting to DataFrame and dropping duplicates on 'Username'
df_final = pd.DataFrame(final_scraped_data)

# Remove any lingering duplicates if a profile was somehow scraped multiple times or partially
# This can happen if a seed user is also found in followers/following and processed differently
if not df_final.empty:
    df_final.drop_duplicates(subset=['Username'], inplace=True, keep='first')
    df_final.set_index('Username', inplace=True) # Set index for easier merging/reordering

# Ensure all required columns exist and order them correctly
required_columns = [
    "Username", # Add Username back as a regular column after reset_index
    "Full Name", "Follower Count", "Following Count",
    "Bio", "WhatsApp Number", "WhatsApp Group Link", "Region", "External Link",
    "Profile URL", "Classification" # Classification is new
]

# Add missing columns with empty string if they don't exist
for col in required_columns:
    if col not in df_final.columns:
        df_final[col] = '' 

# Reorder columns and reset index for final output
df_final = df_final[required_columns].reset_index(drop=True) # Use drop=True as Username is now a regular column


# Save final data to CSV
output_dir = "data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
output_path = os.path.join(output_dir, "instagram_leads.csv")
df_final.to_csv(output_path, index=False)

print(f"✅ Final data saved to {output_path}")