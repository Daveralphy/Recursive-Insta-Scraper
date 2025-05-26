import time
import random
import yaml
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Import the individual scraper functions
# This assumes profile_scraper.py and bio_scraper.py are in the same directory as this file,
# and that their directory is added to the Python path (e.g., by main.py).
# Note: get_bio_data is no longer directly called in this file, but profile_scraper is.
from profile_scraper import get_profile_data # Still needed for the _get_bio_text_for_filtering logic below


# Load configuration
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    # Provide a robust default config if the file is missing
    config = {
        "settings": {"delay_min": 5, "delay_max": 10, "follower_scrape_limit": 500},
        "keywords": ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"] # Reverted to a useful default
    }

DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"].get("follower_scrape_limit", 500)
# Ensure keywords are lowercase for case-insensitive matching
KEYWORDS = [kw.lower() for kw in config.get("keywords", ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"])]


# This helper function is now used to get bio text for filtering,
# by calling the get_profile_data from profile_scraper.
def _get_bio_text_for_filtering(driver, username):
    """
    Navigates to a profile and quickly extracts only the bio text using get_profile_data.
    This is used internally by scrape_followers_and_following for filtering.
    """
    profile_data = get_profile_data(driver, username) # Call the profile scraper to get data
    return profile_data.get("Bio", "") # Return the bio if available, else empty string


def scroll_followers_popup(driver, scroll_attempts=20):
    """
    Scrolls inside the followers or following pop-up window.
    Attempts to scroll until no new content loads or a max attempts limit is reached.
    """
    try:
        # Tries to find the scrollable area, which is usually a div inside the dialog
        # with specific overflow styles or class names that indicate scrollability.
        # Instagram's class names change frequently, so looking for role='dialog' and a scrollable div inside is best.
        # This XPath targets the div inside the dialog that typically contains the scrollable list items.
        scrollable_element_xpath = "//div[@role='dialog']//div[contains(@class, 'x1ja2u2z') and contains(@class, 'x1afv6gd')]/div/div" 
        
        popup_scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, scrollable_element_xpath))
        )
        print("✅ Followers/Following pop-up scrollable area detected!")

        last_height = driver.execute_script("return arguments[0].scrollHeight;", popup_scroll_area)
        scroll_count = 0

        while scroll_count < scroll_attempts:
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
        print("❌ Timeout: Followers/Following pop-up scrollable area not found within 10 seconds. Check XPath.")
    except Exception as e:
        print(f"❌ Error during pop-up scrolling: {e}")

def get_usernames_from_popup(driver):
    """Extracts visible usernames from the followers or following pop-up."""
    usernames = set()
    try:
        # This XPath targets the <a> tags within the list items in the dialog,
        # which usually contain the username in their href, and are specifically the user links.
        # Looking for links directly under divs that are likely user list items.
        username_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//div[contains(@class, 'x9f619')]//a[contains(@href, '/')]"))
        )

        for element in username_elements:
            href = element.get_attribute("href")
            # Filter out non-profile links (e.g., /p/ for posts, /explore/tags/, /direct/, /stories/)
            if href and "/p/" not in href and "/explore/tags/" not in href and "/direct/" not in href and "/stories/" not in href:
                parts = href.strip('/').split('/')
                # The username should be the last part of the URL path before any query parameters
                if len(parts) > 1:
                    username = parts[-1]
                    usernames.add(username)

        print(f"✅ Extracted {len(usernames)} unique usernames from pop-up.")
        return list(usernames)

    except TimeoutException:
        print("❌ Timeout: No username elements found in pop-up within 10 seconds. Check XPath for usernames.")
    except Exception as e:
        print(f"❌ Failed to extract usernames from pop-up: {e}")
        return []

def close_popup(driver):
    """Attempts to close the followers/following pop-up."""
    try:
        # Look for a common close button pattern (e.g., a button with a specific class or an SVG icon)
        # Instagram often uses a button with an 'X' icon or a specific class.
        close_button_xpath = "//div[@role='dialog']//button[contains(@class, '_ablz')] | //div[@role='dialog']//div[@role='button']/*[name()='svg' and @aria-label='Close']"
        
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, close_button_xpath))
        )
        close_button.click()
        print("✅ Pop-up closed using close button.")
    except TimeoutException:
        print("⚠️ Close button not found. Attempting to press ESCAPE key.")
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform() # Use Keys.ESCAPE for robustness
            print("✅ Pop-up closed using ESCAPE key.")
        except Exception as esc_e:
            print(f"❌ Could not close pop-up with ESC key: {esc_e}")
    except Exception as e:
        print(f"❌ Error closing pop-up: {e}")
    finally:
        time.sleep(random.uniform(2, 4)) # Give time for popup to disappear

def scrape_followers_and_following(driver, seed_usernames, profile_scraper_func): # Added profile_scraper_func as a parameter
    """
    Scrapes followers and following lists for seed usernames,
    filters profiles based on keywords in their bios, and returns relevant usernames.
    """
    all_filtered_usernames = set() # This will store only the filtered usernames
    processed_profiles_count = 0

    for username in seed_usernames:
        if processed_profiles_count >= FOLLOWER_LIMIT:
            print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
            break

        print(f"\n🔍 Visiting {username}'s profile to find potential new leads...")
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

        # Wait for the main profile header to load before trying to find buttons
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//header//h2")))
            print(f"  Profile page for {username} loaded.")
        except TimeoutException:
            print(f"  ❌ Timeout: Profile page for {username} did not load in time. Skipping.")
            continue
        except Exception as e:
            print(f"  ❌ Error loading profile page for {username}: {e}. Skipping.")
            continue

        potential_usernames_from_current_profile = set()

        # Scrape Followers
        try:
            print(f"  Attempting to scrape followers for {username}...")
            # Updated XPath for Followers button: Find a link containing 'followers' in href
            # and specifically targeting the 'span' that holds the count or the word 'followers'
            followers_button_xpath = "//a[contains(@href, '/followers/') and contains(@role, 'link')]//span[contains(@class, 'x1i10h5l') or contains(@class, 'xjbqb8b')]"
            followers_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, followers_button_xpath))
            )
            driver.execute_script("arguments[0].click();", followers_button)
            print(f"  Clicked followers button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            scroll_followers_popup(driver, scroll_attempts=20) # Scroll more for followers
            followers_list = get_usernames_from_popup(driver)
            potential_usernames_from_current_profile.update(followers_list)
            print(f"  Collected {len(followers_list)} followers for {username}.")
        except TimeoutException:
            print(f"  ⚠️ Timeout: Followers button not found/clickable for {username}. XPath might be outdated.")
        except Exception as e:
            print(f"  ❌ Error scraping followers for {username}: {e}")
        finally:
            close_popup(driver) # Always try to close the popup

        # Scrape Following
        try:
            if processed_profiles_count >= FOLLOWER_LIMIT:
                print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
                break # Break out of the outer loop (seed_usernames)

            print(f"  Attempting to scrape following for {username}...")
            # Updated XPath for Following button: Similar to followers but with '/following/'
            following_button_xpath = "//a[contains(@href, '/following/') and contains(@role, 'link')]//span[contains(@class, 'x1i10h5l') or contains(@class, 'xjbqb8b')]"
            following_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, following_button_xpath))
            )
            driver.execute_script("arguments[0].click();", following_button)
            print(f"  Clicked following button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            scroll_followers_popup(driver, scroll_attempts=20) # Scroll more for following
            following_list = get_usernames_from_popup(driver)
            potential_usernames_from_current_profile.update(following_list)
            print(f"  Collected {len(following_list)} following for {username}.")
        except TimeoutException:
            print(f"  ⚠️ Timeout: Following button not found/clickable for {username}. XPath might be outdated.")
        except Exception as e:
            print(f"  ❌ Error scraping following for {username}: {e}")
        finally:
            close_popup(driver) # Always try to close the popup

        print(f"  Total unique potential profiles from {username}: {len(potential_usernames_from_current_profile)}")

        # Filter potential profiles based on bio keywords
        for user_to_filter in potential_usernames_from_current_profile:
            if processed_profiles_count >= FOLLOWER_LIMIT:
                print(f"Limit of {FOLLOWER_LIMIT} relevant profiles reached. Stopping.")
                break # Break out of the inner loop (user_to_filter)

            # To avoid re-processing within this function call, and to avoid re-scraping
            # if this user was already found from a previous seed username
            if user_to_filter in all_filtered_usernames:
                continue

            print(f"    - Filtering {user_to_filter}...")
            
            # Call the passed profile_scraper_func to get the bio for filtering
            # Note: profile_scraper_func (which is scrape_profiles) returns a list of dicts.
            # We need to extract the bio from the first (and likely only) dict in that list.
            profile_data_list = profile_scraper_func(driver, [user_to_filter])
            bio_text = ""
            if profile_data_list and profile_data_list[0]:
                bio_text = profile_data_list[0].get("Bio", "") # Assuming Bio is part of profile_data if it were comprehensive

            # Filter based on keywords in the collected bio
            if bio_text and any(keyword in bio_text.lower() for keyword in KEYWORDS):
                all_filtered_usernames.add(user_to_filter)
                processed_profiles_count += 1 # Update count for the limit
                print(f"      ✨ Found relevant profile: {user_to_filter} (Total: {processed_profiles_count})")
            else:
                pass # print(f"      Skipping {user_to_filter} (no keywords found in bio).")

    print(f"\n✅ Scraping complete! {len(all_filtered_usernames)} relevant profiles collected.")
    return list(all_filtered_usernames) # Returns list of filtered usernames only
