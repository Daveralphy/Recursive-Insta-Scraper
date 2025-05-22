import os
import time
import random
import yaml
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from scrapers.profile_scraper import scrape_profiles
from scrapers.bio_scraper import scrape_bios
from scrapers.followers_scraper import scrape_followers

# Load environment variables (credentials)
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Load config settings
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

VISIBLE_BROWSER = config["settings"]["visible_browser"]
SEED_USERNAMES = config["seed_usernames"]

# Initialize Selenium WebDriver
try:
    print("🚀 Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    if not VISIBLE_BROWSER:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

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
    driver.find_element(By.NAME, "username").send_keys(INSTAGRAM_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(INSTAGRAM_PASSWORD)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

    time.sleep(random.randint(5, 10))  # Wait for login to process
    print("✅ Login details entered successfully!")
except Exception as e:
    print(f"❌ Failed to enter login credentials: {e}")
    driver.quit()
    exit()

# Detect and handle Two-Factor Authentication (2FA)
try:
    print("🔍 Checking for 2FA prompt...")
    time.sleep(5)  # Wait for potential 2FA prompt
    security_code_input = driver.find_elements(By.NAME, "verificationCode")

    if security_code_input:
        print("⚠️ Instagram requires Two-Factor Authentication (2FA).")
        security_code = input("🔐 Enter the 2FA code sent to your device: ")

        if security_code:
            security_code_input[0].send_keys(security_code)
            security_code_input[0].send_keys(Keys.RETURN)
            print("✅ Two-factor authentication submitted! Waiting for confirmation...")
        else:
            print("❌ No code entered, exiting.")
            driver.quit()
            exit()

    # Dynamically wait for Instagram to confirm 2FA by detecting URL change
    print("🔍 Waiting for Instagram to confirm login after 2FA...")
    wait_start_time = time.time()

    while True:
        time.sleep(2)  # Small wait before checking again
        current_url = driver.current_url

        if current_url == "https://www.instagram.com/":
            print("✅ 2FA authentication successful! Proceeding to scraping...")
            break

        # Timeout safeguard (prevents infinite waiting)
        if time.time() - wait_start_time > 120:  # Allow up to 2 minutes for authentication
            print("❌ 2FA authentication took too long! Exiting...")
            driver.quit()
            exit()

except Exception as e:
    print(f"⚠️ Could not detect 2FA input field: {e}")

# Confirm login success before scraping
try:
    time.sleep(5)  # Allow Instagram to process login
    current_url = driver.current_url
    print(f"🔗 Current URL after login: {current_url}")

    if "accounts/login" in current_url:
        print("❌ Login failed! Verify credentials or complete security checks.")
        driver.quit()
        exit()
    print("✅ Login successful!")
except Exception as e:
    print(f"❌ Unexpected login failure: {e}")
    driver.quit()
    exit()

# Start scraping process using the same WebDriver session
print("🚀 Starting follower scraping...")
followers = scrape_followers(driver)

print("🚀 Scraping profiles...")
scrape_profiles(driver, followers)  # Pass WebDriver session

print("🚀 Scraping bios...")
scrape_bios(driver)  # Pass WebDriver session

# Close browser session after all scraping is done
driver.quit()
print("✅ Scraping process completed successfully!")
