import time
import random
import yaml
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Ensure correct import paths for other scraper modules
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scrapers')))

# Corrected Import: Import 'scrape_profiles' as it's the main profile scraper function
from profile_scraper import scrape_profiles


# Load configuration (this file will still load its own config as per your request)
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found. Please create a config.yaml file.")
    # Provide a robust default config if the file is missing
    config = {
        "settings": {
            "delay_min": 5,
            "delay_max": 10,
            "follower_scrape_limit": 500,
            "unlimited_follower_scrape": False, # New config setting for UNLIMITED mode
            "scroll_attempts_max": 20, # Max attempts if not in unlimited mode
            "recursion_depth": 1 # Default for recursion
        },
        "keywords": ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"]
    }

# Global variables read from config (as in your provided working file)
DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"].get("follower_scrape_limit", 500)
UNLIMITED_FOLLOWER_SCRAPE = config["settings"].get("unlimited_follower_scrape", False)
SCROLL_ATTEMPTS_MAX = config["settings"].get("scroll_attempts_max", 20)
RECURSION_DEPTH = config["settings"].get("recursion_depth", 1) # Get recursion depth from config

# Ensure keywords are lowercase for case-insensitive matching (used for light_scrape_and_filter_profile)
LIGHT_SCRAPE_KEYWORDS = [kw.lower() for kw in config.get("keywords", ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"])]


# This function now performs the light scrape for filtering by calling scrape_profiles
# and extracts the relevant fields. It now returns the full profile_data if relevant.
def light_scrape_and_filter_profile(driver, username, config_for_keywords): # Added config_for_keywords
    """
    Performs a light scrape to check for keywords in the bio/full name/external link.
    Returns the profile_data dictionary if relevant, None otherwise.
    This uses the 'scrape_profiles' function from profile_scraper for the light scrape,
    but only processes a subset of its output for relevance.
    """
    # Use keywords from the passed config_for_keywords
    current_light_scrape_keywords = [kw.lower() for kw in config_for_keywords.get("keywords", [])]

    # Use scrape_profiles to get the full profile data (which includes bio, full name, external link)
    # This is effectively a "light" scrape for filtering purposes here.
    profile_data_list = scrape_profiles(driver, [username])

    if not profile_data_list:
        return None # Profile not found or couldn't be scraped

    profile_data = profile_data_list[0] # We only scraped one username

    bio = profile_data.get("Bio", "").lower()
    full_name = profile_data.get("Full Name", "").lower()
    external_link = profile_data.get("External Link", "").lower()

    text_to_filter = f"{bio} {full_name} {external_link}"

    # Check if any of the defined keywords are present
    if any(keyword in text_to_filter for keyword in current_light_scrape_keywords):
        print(f"        '{username}' is relevant (matched keyword).")
        return profile_data # Return the full profile data dictionary
    else:
        # print(f"        '{username}' is NOT relevant (no keyword match).") # Uncomment for verbose filtering
        return None


def scroll_followers_popup(driver, scroll_attempts):
    """
    Scrolls inside the followers or following pop-up window.
    Attempts to scroll until no new content loads or a max attempts limit is reached.
    Uses the original working XPath for the scrollable area.
    """
    try:
        # ORIGINAL WORKING XPATH for the scrollable area from your previous file
        scrollable_element_xpath = "//div[@role='dialog']//div[contains(@class, 'x1ja2u2z') and contains(@class, 'x1afv6gd')]/div/div"

        popup_scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, scrollable_element_xpath))
        )
        print("✅ Followers/Following pop-up scrollable area detected!")

        last_height = driver.execute_script("return arguments[0].scrollHeight;", popup_scroll_area)
        current_scroll_attempts = 0

        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", popup_scroll_area)
            time.sleep(random.uniform(2, 4)) # Allow content to load

            new_height = driver.execute_script("return arguments[0].scrollHeight;", popup_scroll_area)

            if UNLIMITED_FOLLOWER_SCRAPE:
                if new_height == last_height:
                    print(f"     Reached end of scrollable content in UNLIMITED mode.")
                    break # No new content loaded, stop scrolling
            else: # LIMIT mode
                current_scroll_attempts += 1
                if new_height == last_height or current_scroll_attempts >= scroll_attempts:
                    print(f"     Reached end of scrollable content or max scrolls ({current_scroll_attempts}/{scroll_attempts}).")
                    break # No new content loaded or max attempts reached

            last_height = new_height
            print(f"     Scrolled popup. Current height: {new_height}. Last height: {last_height}. Attempts: {current_scroll_attempts}")

        print(f"✅ Finished scrolling popup. Total scrolls: {current_scroll_attempts}")

    except TimeoutException:
        print("❌ Timeout: Followers/Following pop-up scrollable area not found within 10 seconds. Check XPath.")
    except Exception as e:
        print(f"❌ Error during pop-up scrolling: {e}")

def get_usernames_from_popup(driver):
    """
    Extracts visible usernames from the followers or following pop-up.
    Uses the original working XPath for username elements.
    """
    usernames = set()
    try:
        # ORIGINAL WORKING XPATH for username elements from your previous file
        username_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//div[contains(@class, 'x9f619')]//a[contains(@href, '/')]"))
        )

        for element in username_elements:
            href = element.get_attribute("href")
            # Filter out non-profile links (e.g., /p/ for posts, /explore/tags/, /direct/, /stories/)
            if href and "/p/" not in href and "/explore/tags/" not in href and "/direct/" not in href and "/stories/" not in href and "/reels/" not in href: # Added /reels/
                parts = href.strip('/').split('/')
                # The username should be the last part of the URL path before any query parameters
                if len(parts) > 1:
                    username = parts[-1]
                    usernames.add(username)

        print(f"✅ Extracted {len(usernames)} unique usernames from pop-up.")
        return list(usernames)

    except TimeoutException:
        print("❌ Timeout: No username elements found in pop-up within 10 seconds. Check XPath for usernames.")
        return []
    except Exception as e:
        print(f"❌ Failed to extract usernames from pop-up: {e}")
        return []

def close_popup(driver):
    """
    Attempts to close the followers/following pop-up.
    Uses the original working XPath for the close button, prioritizing ESCAPE.
    """
    try:
        # Prioritize the ESCAPE key as it's often the most reliable way to close pop-ups.
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        print("✅ Pop-up closed using ESCAPE key.")
    except Exception as esc_e:
        print(f"⚠️ Could not close pop-up with ESC key: {esc_e}. Trying close button...")
        try:
            # ORIGINAL WORKING XPATH for close button from your previous file
            close_button_xpath = "//div[@role='dialog']//button[contains(@class, '_ablz')] | //div[@role='dialog']//div[@role='button']/*[name()='svg' and @aria-label='Close']"

            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, close_button_xpath))
            )
            close_button.click()
            print("✅ Pop-up closed using close button.")
        except TimeoutException:
            print("❌ Timeout: Close button not found. Pop-up might still be open.")
        except Exception as e:
            print(f"❌ Error closing pop-up with button: {e}")
    finally:
        time.sleep(random.uniform(2, 4)) # Give time for popup to disappear


# Modified signature to accept process_and_live_export_profile_func and config
def scrape_followers_and_following(driver, seed_usernames, process_and_live_export_profile_func, scrape_profiles_function, config_from_main, current_depth=0, scraped_usernames_set=None):
    """
    Scrapes followers and following lists for seed usernames (STEP 2),
    filters profiles based on keywords in their bios using a light scrape (STEP 3),
    and live-exports relevant profiles. Includes recursion.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        seed_usernames (list): List of usernames to expand from at this depth.
        process_and_live_export_profile_func (function): The function to call for live export.
        scrape_profiles_function (function): The function used to scrape full profile data.
        config_from_main (dict): The loaded configuration dictionary from main.py.
        current_depth (int): The current recursion depth.
        scraped_usernames_set (set, optional): A set of all usernames already processed
                                            across all recursion depths. Defaults to None.
    Returns:
        None: This function now handles live export internally and does not return a list.
    """
    if scraped_usernames_set is None:
        scraped_usernames_set = set() # Initialize an empty set if not provided

    # Add current seed usernames to the processed set to avoid immediate re-processing
    scraped_usernames_set.update(seed_usernames)

    # RECURSION_DEPTH is a global variable in this file, read from its own config load.
    # This aligns with the user's provided 'working' file structure.
    if current_depth > RECURSION_DEPTH:
        print(f"Max recursion depth ({RECURSION_DEPTH}) reached. Stopping.")
        return # No return value, as we're live exporting

    print(f"\n✨ Entering recursion depth: {current_depth} for {len(seed_usernames)} seed(s).")

    # This list will hold usernames that are relevant and will be used as seeds for the next recursion depth
    next_level_seed_usernames = set()

    for username in seed_usernames:
        # Check if this username has already been processed and exported in a prior depth
        if username in scraped_usernames_set and current_depth > 0:
            continue # Already processed, skip this user for expansion at this depth

        print(f"    Processing followers/following for @{username} (Depth: {current_depth})")

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

        try:
            # Wait for the main profile header to load before trying to find buttons
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//header//h2")))
            print(f"    Profile page for {username} loaded.")
        except TimeoutException:
            # MODIFIED BEHAVIOR: Print warning, but do NOT 'continue'.
            # This allows the code to proceed and try clicking the follower/following buttons.
            print(f"    ⚠️ Warning: Profile page for {username} did not load in time. Attempting to proceed with button clicks anyway.")
        except Exception as e:
            # For more critical errors that prevent any interaction with the profile, skip the user.
            print(f"    ❌ Critical Error loading profile page for {username}: {e}. Skipping this user for current depth's button clicks.")
            continue # Skip to the next seed_username if there's a fundamental issue with the profile page.

        # --- STEP 2: Scrape Followers ---
        # Introduce a flag to know if followers were successfully scraped.
        followers_scraped_successfully = False
        try:
            print(f"    Attempting to scrape followers for {username}...")
            # --- NEW XPATH for Followers button ---
            followers_button_xpath = "//a[contains(@href, '/followers/') and (./div/span/span[contains(text(), 'followers') or contains(text(), 'Followers')])]"
            followers_button_xpath_fallback = "//a[contains(@href, '/followers/') and (@role='link' or contains(., 'followers') or contains(., 'Followers'))]"

            followers_button = None
            try:
                followers_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, followers_button_xpath))
                )
            except TimeoutException:
                print("         Trying fallback XPath for followers button...")
                followers_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, followers_button_xpath_fallback))
                )

            driver.execute_script("arguments[0].click();", followers_button)
            print(f"    Clicked followers button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            # Adjust scroll_attempts based on UNLIMITED mode
            actual_scroll_attempts = float('inf') if UNLIMITED_FOLLOWER_SCRAPE else SCROLL_ATTEMPTS_MAX
            scroll_followers_popup(driver, scroll_attempts=actual_scroll_attempts) # Pass config not needed here as UNLIMITED_FOLLOWER_SCRAPE is global

            followers_list = get_usernames_from_popup(driver)
            print(f"    Collected {len(followers_list)} followers for {username}.")

            # Filter and live-export profiles
            processed_count_this_section = 0
            for follower_username in followers_list:
                if processed_count_this_section >= FOLLOWER_LIMIT:
                    print(f"    Reached FOLLOWER_LIMIT ({FOLLOWER_LIMIT}) for profiles from this section.")
                    break

                # Only process if not already scraped (from current or previous depths)
                if follower_username not in scraped_usernames_set:
                    # light_scrape_and_filter_profile now returns the profile data dictionary
                    relevant_profile_data = light_scrape_and_filter_profile(driver, follower_username, config_from_main) # Pass config_from_main for keywords
                    if relevant_profile_data:
                        # Perform live export for this relevant profile
                        process_and_live_export_profile_func(relevant_profile_data, config_from_main, scraped_usernames_set)
                        next_level_seed_usernames.add(follower_username) # Add to next recursion seeds
                        # scraped_usernames_set.add(follower_username) # This is handled by process_and_live_export_profile_func

                    processed_count_this_section += 1 # Count every user *considered* for processing
            followers_scraped_successfully = True # Set flag to True if this block runs without critical error

        except TimeoutException as e:
            print(f"    ⚠️ Timeout: Followers button not found/clickable or pop-up not visible for {username}. Error: {e}")
        except NoSuchElementException as e:
            print(f"    ⚠️ Element not found: Followers button or pop-up element for {username}. Error: {e}")
        except Exception as e:
            print(f"    ❌ Error scraping followers for {username}: {e}")
        finally:
            if followers_scraped_successfully: # Only close if a popup likely opened
                close_popup(driver)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX)) # Add delay after trying to close popup or moving on


        # --- STEP 2: Scrape Following ---
        # The logic here is similar to followers, ensuring it runs independently.
        following_scraped_successfully = False
        try:
            print(f"    Attempting to scrape following for {username}...")
            # --- NEW XPATH for Following button ---
            following_button_xpath = "//a[contains(@href, '/following/') and (./div/span/span[contains(text(), 'following') or contains(text(), 'Following')])]"
            following_button_xpath_fallback = "//a[contains(@href, '/following/') and (@role='link' or contains(., 'following') or contains(., 'Following'))]"

            following_button = None
            try:
                following_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, following_button_xpath))
                )
            except TimeoutException:
                print("         Trying fallback XPath for following button...")
                following_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, following_button_xpath_fallback))
                )

            driver.execute_script("arguments[0].click();", following_button)
            print(f"    Clicked following button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            # Adjust scroll_attempts based on UNLIMITED mode
            actual_scroll_attempts = float('inf') if UNLIMITED_FOLLOWER_SCRAPE else SCROLL_ATTEMPTS_MAX
            scroll_followers_popup(driver, scroll_attempts=actual_scroll_attempts) # Pass config not needed here

            following_list = get_usernames_from_popup(driver)
            print(f"    Collected {len(following_list)} following for {username}.")

            # Filter and live-export profiles
            processed_count_this_section = 0
            for following_username in following_list:
                if processed_count_this_section >= FOLLOWER_LIMIT:
                    print(f"    Reached FOLLOWER_LIMIT ({FOLLOWER_LIMIT}) for profiles from this section.")
                    break

                # Only process if not already scraped (from current or previous depths)
                if following_username not in scraped_usernames_set:
                    # light_scrape_and_filter_profile now returns the profile data dictionary
                    relevant_profile_data = light_scrape_and_filter_profile(driver, following_username, config_from_main) # Pass config_from_main
                    if relevant_profile_data:
                        # Perform live export for this relevant profile
                        process_and_live_export_profile_func(relevant_profile_data, config_from_main, scraped_usernames_set)
                        next_level_seed_usernames.add(following_username) # Add to next recursion seeds
                        # scraped_usernames_set.add(following_username) # This is handled by process_and_live_export_profile_func

                    processed_count_this_section += 1 # Count every user *considered* for processing
            following_scraped_successfully = True # Set flag to True if this block runs without critical error

        except TimeoutException as e:
            print(f"    ⚠️ Timeout: Following button not found/clickable or pop-up not visible for {username}. Error: {e}")
        except NoSuchElementException as e:
            print(f"    ⚠️ Element not found: Following button or pop-up element for {username}. Error: {e}")
        except Exception as e:
            print(f"    ❌ Error scraping following for {username}: {e}")
        finally:
            if following_scraped_successfully: # Only close if a popup likely opened
                close_popup(driver)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX)) # Add delay after trying to close popup or moving on


    # Recursion: Scrape followers of newly found relevant profiles
    if next_level_seed_usernames and current_depth < RECURSION_DEPTH:
        print(f"\n    Recursion: Scraping followers of {len(next_level_seed_usernames)} newly found relevant profiles (Depth: {current_depth + 1})...")

        # Pass the accumulated scraped_usernames_set to the next recursion level
        # This set ensures we don't re-process users across depths
        updated_scraped_usernames_set = scraped_usernames_set.union(next_level_seed_usernames)

        scrape_followers_and_following(
            driver,
            list(next_level_seed_usernames), # Use the newly found relevant users as seeds for next depth
            process_and_live_export_profile_func, # Pass the live export function
            scrape_profiles_function,
            config_from_main, # Pass config from main
            current_depth + 1,
            updated_scraped_usernames_set # Pass the updated set
        )

    return # This function now handles live export internally and does not return a list.