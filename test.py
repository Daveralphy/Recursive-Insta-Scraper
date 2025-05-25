import time
import random
import re # Import regex module
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- Configuration (You'll need to install these) ---
# 1. Install Selenium: pip install selenium
# 2. Download ChromeDriver: https://chromedriver.chromium.org/downloads
#    Make sure the ChromeDriver version matches your Chrome browser version.
#    Place chromediver.exe (or chromedriver) in a directory included in your system's PATH,
#    or specify its path directly: service=Service('/path/to/chromedriver')

# A list of common user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/108.0.1462.54",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/108.0",
]

def setup_driver():
    """Sets up and returns a configured Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # Run browser without a UI
    options.add_argument("--no-sandbox") # Required for some environments
    options.add_argument("--disable-dev-shm-usage") # Required for some environments
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}") # Rotate user-agents
    options.add_argument("--window-size=1920,1080") # Set a fixed window size for consistent rendering
    # Suppress console errors from Chrome itself (optional, but can clean up output)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print(f"Error setting up WebDriver: {e}")
        print("Please ensure ChromeDriver is installed and its version matches your Chrome browser,")
        print("and that it's in your system's PATH or specified correctly.")
        return None

def instagram_login(driver, username, password):
    """
    Attempts to log into Instagram.
    Handles 'Save Info' and 'Turn on Notifications' pop-ups.
    Includes a basic placeholder for 2FA handling.
    """
    print("Attempting to log into Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")

    try:
        # Wait for username and password fields to be present
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")

        username_field.send_keys(username)
        password_field.send_keys(password)

        # Find and click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()

        # --- Handle post-login pop-ups ---
        # Wait for the page to load after login, typically by looking for the home feed or profile icon
        WebDriverWait(driver, 20).until(
            EC.url_contains("instagram.com") and
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@role, 'dialog')]//button[text()='Not Now']")), # For "Save Info" or "Turn on Notifications"
                EC.presence_of_element_located((By.XPATH, "//a[@href='/']")) # For home feed link
            )
        )

        # Handle "Save Info" pop-up (if it appears)
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@role, 'dialog')]//button[text()='Not Now']"))
            )
            not_now_button.click()
            print("Clicked 'Not Now' on Save Info pop-up.")
            time.sleep(random.uniform(1, 2)) # Small delay after clicking
        except TimeoutException:
            print("No 'Save Info' pop-up found or it didn't appear.")

        # Handle "Turn on Notifications" pop-up (if it appears)
        try:
            not_now_button_notifications = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@role, 'dialog')]//button[text()='Not Now']"))
            )
            not_now_button_notifications.click()
            print("Clicked 'Not Now' on Turn on Notifications pop-up.")
            time.sleep(random.uniform(1, 2)) # Small delay after clicking
        except TimeoutException:
            print("No 'Turn on Notifications' pop-up found or it didn't appear.")

        # --- 2FA Handling (Manual Intervention) ---
        # This is a basic placeholder. Fully automated 2FA is complex and not recommended for simple scripts.
        try:
            # Look for common 2FA elements (e.g., input for code, verify button)
            two_fa_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Security Code']"))
            )
            print("\n--- 2FA CHALLENGE DETECTED ---")
            print("Please check your phone/email for the 2FA code.")
            verification_code = input("Enter the 2FA code manually here: ")
            two_fa_input.send_keys(verification_code)

            verify_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Confirm']")) # Or 'Verify', 'Next'
            )
            verify_button.click()
            print("2FA code submitted. Waiting for navigation...")
            WebDriverWait(driver, 15).until(EC.url_contains("instagram.com")) # Wait for successful 2FA
            print("2FA successful.")
        except TimeoutException:
            print("No 2FA challenge detected or handled.")
        except Exception as e:
            print(f"An error occurred during 2FA handling: {e}")


        print("Login successful.")
        return True

    except TimeoutException:
        print("Login failed: Username/password fields or login button not found within timeout.")
        print("Current page source for debugging login issue:")
        print(driver.page_source[:2000])
        return False
    except NoSuchElementException as e:
        print(f"Login failed: Element not found - {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return False


# --- Helper function to scrape a single profile ---
def scrape_instagram_profile(driver, username):
    """
    Scrapes key information from a single Instagram profile using an already logged-in headless browser.
    Note: Instagram's structure changes frequently. Element selectors may need updating.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"\nAttempting to scrape: {profile_url}")

    profile_data = {
        "Username": username,
        "Full Name": "",
        "Follower Count": "0",
        "Following Count": "0",
        "Bio": "",
        "External Link": "",
        "Profile URL": profile_url,
        "WhatsApp Number": "", # Requires advanced parsing
        "Region": ""           # Requires advanced parsing/inference
    }

    try:
        driver.get(profile_url)

        # --- IMPORTANT: Wait for elements to be present ---
        # Instagram's HTML structure changes frequently. If the script times out,
        # you MUST manually inspect the Instagram page in your browser's developer tools
        # to find the current, correct XPATH or CSS selectors.

        # Initial wait: Wait for a common element in the profile header to load,
        # such as the username (h2) or the main profile content area.
        # This is a more generic XPath for the username h2, which is often a good indicator
        # that the main profile content has loaded.
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//header//h2"))
        )
        print(f"  Profile page for {username} loaded.")

        # 1. Extract Full Name
        try:
            # The full name is often a div or span element that is a sibling to the username h2,
            # or within a common parent element in the profile header.
            # This XPath attempts to find the full name based on its common structural position.
            # Instagram often uses a specific class for the full name.
            full_name_element = driver.find_element(By.XPATH, "//h2[contains(@class, 'x1lli2ws')]") # This is a common class for the username/full name area
            profile_data["Full Name"] = full_name_element.text
        except NoSuchElementException:
            print(f"  Full name not found for {username}. (XPath might be outdated)")


        # 2. Extract Follower and Following Counts
        # These are usually within <a> tags with specific hrefs or aria-labels.
        # The exact number is often in the 'title' attribute or the text content.
        try:
            # Find the element containing follower count. It's usually an <a> tag linking to /followers/.
            # The number itself is often in a child <span>.
            follower_count_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers/')]/span/span"))
            )
            follower_count = follower_count_element.get_attribute("title") or follower_count_element.text
            profile_data["Follower Count"] = follower_count.replace(',', '')
        except TimeoutException:
            print(f"  Follower count element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Follower count element not found for {username}. (XPath might be outdated)")

        try:
            # Find the element containing following count. It's usually an <a> tag linking to /following/.
            # The number itself is often in a child <span>.
            following_count_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following/')]/span/span"))
            )
            following_count = following_count_element.get_attribute("title") or following_count_element.text
            profile_data["Following Count"] = following_count.replace(',', '')
        except TimeoutException:
            print(f"  Following count element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Following count element not found for {username}. (XPath might be outdated)")


        # 3. Extract Bio
        try:
            # Bio is often a text block. Try to find a div or span that contains the main bio text.
            # This XPath looks for a div that is a sibling to the profile header and contains text.
            bio_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x7a106z') and contains(@class, 'x972fbf') and contains(@class, 'xcfux6l')]")) # Common bio container
            )
            profile_data["Bio"] = bio_element.text
        except TimeoutException:
            print(f"  Bio element not found/loaded for {username}. (XPath might be outdated)")
        except NoSuchElementException:
            print(f"  Bio not found for {username}. (XPath might be outdated)")

        # 4. Extract External Link
        try:
            # External link is typically an <a> tag with target="_blank" and rel="nofollow".
            external_link_element = driver.find_element(By.XPATH, "//a[contains(@target, '_blank') and contains(@rel, 'nofollow')]")
            profile_data["External Link"] = external_link_element.get_attribute("href")
        except NoSuchElementException:
            print(f"  External link not found for {username}. (XPath might be outdated)")

        # 5. WhatsApp Number & Region (These are much harder and require custom logic)
        # These fields are not standard Instagram fields and require parsing the bio or external links.
        # This part is highly unreliable without specific cues from the profile content.

        # Attempt to extract WhatsApp Number from Bio using regex
        # This regex tries to capture common phone number formats, including international prefixes
        whatsapp_pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,6}"
        phone_numbers = re.findall(whatsapp_pattern, profile_data["Bio"])
        if phone_numbers:
            # Take the first found number as a potential WhatsApp number
            profile_data["WhatsApp Number"] = phone_numbers[0]
            print(f"  Potential WhatsApp number found: {profile_data['WhatsApp Number']}")


        print(f"  Scraped data for {username}:")
        for key, value in profile_data.items():
            print(f"    {key}: {value}")

    except TimeoutException:
        print(f"Timeout while loading page for {username}. This often means the page did not load completely within the given time, or the initial selectors are incorrect.")
        print("  Current page source for debugging:")
        print(driver.page_source[:2000]) # Print first 2000 characters of page source for debugging
    except Exception as e:
        print(f"An unexpected error occurred while scraping {username}: {e}")

    return profile_data

# --- Main execution ---
if __name__ == "__main__":
    print("--- Instagram Scraper with Login ---")
    print("WARNING: Using this script violates Instagram's Terms of Service and may lead to account bans.")
    print("It also requires you to provide your Instagram credentials, which carries security risks.")
    print("Use a dedicated, non-essential account if possible.")
    print("-" * 40)

    insta_username = input("Enter your Instagram username: ")
    insta_password = input("Enter your Instagram password: ")

    driver = setup_driver()
    if not driver:
        exit("Failed to initialize WebDriver. Exiting.")

    if not instagram_login(driver, insta_username, insta_password):
        driver.quit()
        exit("Login failed. Please check your credentials or try again later.")

    seed_usernames = ["gsmplusvrsac", "iphone.miami"]
    all_scraped_data = []

    for username in seed_usernames:
        data = scrape_instagram_profile(driver, username)
        all_scraped_data.append(data)
        # Introduce a random delay between requests to avoid rate limiting
        time.sleep(random.uniform(5, 10)) # Wait 5-10 seconds

    driver.quit() # Close the browser after all scraping is done

    # You can then process all_scraped_data (e.g., save to CSV)
    import pandas as pd
    df = pd.DataFrame(all_scraped_data)
    print("\n--- Scraped Data DataFrame ---")
    print(df)
    df.to_csv("instagram_profiles.csv", index=False)
    print("\nData saved to instagram_profiles.csv")
