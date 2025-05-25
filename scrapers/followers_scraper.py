import time
import random
import yaml
import re # Added for potential future advanced filtering, not strictly used in current bio text
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Load configuration
# Assuming config.yaml is in the root directory accessible from where main.py runs
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    config = {
        "settings": {"delay_min": 5, "delay_max": 10, "follower_scrape_limit": 50},
        # Default KEYWORDS for safety if not in config
        "keywords": ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"]
    }

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"].get("follower_scrape_limit", 50) # Default to 50 if not specified
KEYWORDS = config.get("keywords", ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"])

# Helper function to get *only* the bio text from a profile page for filtering purposes
def _get_bio_text_for_filtering(driver, username):
    """
    Navigates to a profile and quickly extracts only the bio text.
    This is used internally by scrape_followers_and_following for filtering,
    not for comprehensive bio data collection.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    driver.get(profile_url)
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    bio_text = ""
    try:
        wait = WebDriverWait(driver, 10)
        # Wait for a prominent element in the profile header
        wait.until(EC.presence_of_element_located((By.XPATH, "//header//h2")))

        # Use the more robust XPath for bio text
        bio_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x7a106z') and contains(@class, 'x972fbf') and contains(@class, 'xcfux6l')]")))
        bio_text = bio_element.text.strip()
    except TimeoutException:
        # print(f"  (Filter) Bio element not found/loaded for {username}. Skipping bio filter.")
        pass # Suppress detailed error for quick filtering
    except NoSuchElementException:
        # print(f"  (Filter) Bio not found for {username}. Skipping bio filter.")
        pass # Suppress detailed error for quick filtering
    except Exception as e:
        print(f"  (Filter) Unexpected error getting bio for {username}: {e}")

    return bio_text

def scroll_followers_popup(driver, limit_scrolls=10):
    """
    Scrolls inside the followers or following pop-up window until no new content loads
    or a scroll limit is reached.
    """
    try:
        # The scrollable element is often an inner div within the main dialog
        # Find the specific scrollable element by role, attribute, or class
        # This XPath targets the div inside the dialog that typically contains the scrollable list items.
        scrollable_element_xpath = "//div[@role='dialog']//div[@class='_aano']" # Common class for scrollable content on Instagram popups

        popup_scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, scrollable_element_xpath))
        )
        print("✅ Followers/Following pop-up scrollable area detected!")

        last_height = driver.execute_script("return arguments[0].scrollHeight;", popup_scroll_area)
        scroll_count = 0

        while scroll_count < limit_scrolls: # Limit scrolls to prevent infinite loops on very long lists
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", popup_scroll_area)
            time.sleep(random.uniform(2, 4)) # Allow content to load

            new_height = driver.execute_script("return arguments[0].scrollHeight;", popup_scroll_area)
            if new_height == last_height:
                print(f"  Reached end of scrollable content or max scrolls ({scroll_count}).")
                break # No new content loaded, stop scrolling

            last_height = new_height
            scroll_count += 1
            print(f"  Scrolled popup {scroll_count} times...")
        
        print(f"✅ Finished scrolling popup. Total scrolls: {scroll_count}")

    except TimeoutException:
        print("❌ Timeout: Followers/Following pop-up scrollable area not found within 10 seconds.")
    except Exception as e:
        print(f"❌ Error during pop-up scrolling: {e}")

def get_usernames_from_popup(driver):
    """Extracts visible usernames from the followers or following pop-up."""
    usernames = set()
    try:
        # This XPath targets the <a> tags within the scrollable list items in the dialog,
        # which usually contain the username in their href.
        username_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//li//a[contains(@href, '/')]"))
        )

        for element in username_elements:
            href = element.get_attribute("href")
            if href and "/p/" not in href and "/explore/tags/" not in href and "/direct/" not in href: # Exclude post links, tag links, etc.
                parts = href.strip('/').split('/')
                if len(parts) > 1:
                    username = parts[-1] # Get the last part of the URL path
                    usernames.add(username)

        print(f"✅ Extracted {len(usernames)} unique usernames from pop-up.")
        return list(usernames)

    except TimeoutException:
        print("❌ Timeout: No username elements found in pop-up within 10 seconds.")
    except Exception as e:
        print(f"❌ Failed to extract usernames from pop-up: {e}")
        return []

def close_popup(driver):
    """Attempts to close the followers/following pop-up."""
    try:
        # Try to find a close button (often an X icon or similar with a specific aria-label or role)
        # Or, try pressing ESCAPE key which often closes modals.
        close_button_xpath = "//div[@role='dialog']//button[contains(@class, '_ablz') or contains(@class, '_acan')]" # Common close button classes/patterns
        
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, close_button_xpath))
        )
        close_button.click()
        print("✅ Pop-up closed using close button.")
    except TimeoutException:
        print("⚠️ Close button not found. Attempting to press ESCAPE key.")
        try:
            # Using ActionChains to send ESCAPE key
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).send_keys(By.ESCAPE).perform()
            print("✅ Pop-up closed using ESCAPE key.")
        except Exception as esc_e:
            print(f"❌ Could not close pop-up with ESCAPE key: {esc_e}")
    except Exception as e:
        print(f"❌ Error closing pop-up: {e}")
    finally:
        time.sleep(random.uniform(2, 4)) # Give time for popup to disappear

def scrape_followers_and_following(driver, seed_usernames):
    """
    Scrapes followers and following lists for seed usernames,
    filters profiles based on keywords in their bios, and returns relevant usernames.
    """
    all_filtered_usernames = set()
    processed_profiles_count = 0 # Track how many profiles we've processed for the limit

    for username in seed_usernames:
        if processed_profiles_count >= FOLLOWER_LIMIT:
            print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
            break

        print(f"\n🔍 Visiting {username}'s profile to find potential new leads...")
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

        potential_usernames_from_current_profile = set()

        # Scrape Followers
        try:
            print(f"  Attempting to scrape followers for {username}...")
            followers_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]"))
            )
            driver.execute_script("arguments[0].click();", followers_button)
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            scroll_followers_popup(driver, limit_scrolls=20) # Scroll more for followers
            followers_list = get_usernames_from_popup(driver)
            potential_usernames_from_current_profile.update(followers_list)
            print(f"  Collected {len(followers_list)} followers for {username}.")
        except TimeoutException:
            print(f"  Followers button not found/clickable for {username}.")
        except Exception as e:
            print(f"  Error scraping followers for {username}: {e}")
        finally:
            close_popup(driver) # Always try to close the popup

        # Scrape Following
        try:
            if processed_profiles_count >= FOLLOWER_LIMIT: # Check limit again before next step
                print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
                break
            print(f"  Attempting to scrape following for {username}...")
            following_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following/')]"))
            )
            driver.execute_script("arguments[0].click();", following_button)
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            scroll_followers_popup(driver, limit_scrolls=20) # Scroll more for following
            following_list = get_usernames_from_popup(driver)
            potential_usernames_from_current_profile.update(following_list)
            print(f"  Collected {len(following_list)} following for {username}.")
        except TimeoutException:
            print(f"  Following button not found/clickable for {username}.")
        except Exception as e:
            print(f"  Error scraping following for {username}: {e}")
        finally:
            close_popup(driver) # Always try to close the popup

        print(f"  Total unique potential profiles from {username}: {len(potential_usernames_from_current_profile)}")

        # Filter potential profiles based on bio keywords
        for user_to_filter in potential_usernames_from_current_profile:
            if processed_profiles_count >= FOLLOWER_LIMIT:
                print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
                break

            if user_to_filter in all_filtered_usernames: # Skip already processed
                continue

            print(f"    - Filtering {user_to_filter}...")
            bio_text = _get_bio_text_for_filtering(driver, user_to_filter)
            if any(keyword in bio_text.lower() for keyword in KEYWORDS):
                all_filtered_usernames.add(user_to_filter)
                processed_profiles_count += 1
                print(f"      ✨ Found relevant profile: {user_to_filter} (Total: {processed_profiles_count})")
            else:
                pass
                # print(f"      Skipping {user_to_filter} (no keywords found).")

    print(f"\n✅ Scraping complete! {len(all_filtered_usernames)} relevant profiles collected.")
    return list(all_filtered_usernames) # Returns filtered usernames for further comprehensive scraping
