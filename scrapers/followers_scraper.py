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
            "scroll_attempts_max": 50, # Set to 50 as per your previous log output, for fixed scrolls
            "recursion_depth": 1 # Default for recursion
        },
        "keywords": ["celulares", "accesorios", "mayorista", "distribuidor", "smartphone", "movil", "telefone", "tecnologia"]
    }

# Global variables read from config (as in your provided working file)
DELAY_MIN = config["settings"]["delay_min"]
DELAY_MAX = config["settings"]["delay_max"]
FOLLOWER_LIMIT = config["settings"].get("follower_scrape_limit", 500)
UNLIMITED_FOLLOWER_SCRAPE = config["settings"].get("unlimited_follower_scrape", False) # FORCED to False for fixed scrolls
SCROLL_ATTEMPTS_MAX = config["settings"].get("scroll_attempts_max", 50) # Using this as the fixed scroll count
RECURSION_DEPTH = config["settings"].get("recursion_depth", 5) # Get recursion depth from config

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
        # print(f"        '{username}' is NOT relevant (no keyword match). # Uncomment for verbose filtering
        return None

def scroll_followers_popup(driver, scroll_attempts):
    """
    Scrolls inside the followers or following pop-up window by scrolling the last element into view.
    It will keep scrolling as long as new content is loaded or until it hits scroll_attempts.
    """
    try:
        # Using the CSS Selector you provided for the scrollable area
        scrollable_element_selector = "body > div.x1n2onr6.xzkaem6 > div:nth-child(2) > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > div > div > div > div > div.x7r02ix.xf1ldfh.x131esax.xdajt7p.xxfnqb6.xb88tzc.xw2csxc.x1odjw0f.x5fp0pe > div > div > div.xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6 > div:nth-child(1) > div"

        popup_scroll_area = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_element_selector))
        )
        print("✅ Followers/Following pop-up scrollable area detected using CSS selector!")

        # Initial collection of usernames
        initial_usernames_list = get_usernames_from_popup(driver)
        all_collected_usernames = set(initial_usernames_list) # Use a set to store all unique usernames collected

        print(f"    Initial unique usernames found: {len(all_collected_usernames)}")
        
        print(f"    Starting element-based scrolling attempts (max {SCROLL_ATTEMPTS_MAX})...")

        last_known_username_count = len(all_collected_usernames)
        scroll_count = 0
        stagnation_count = 0 # To detect if scrolling isn't loading new content

        while scroll_count < scroll_attempts:
            try:
                # IMPORTANT FIX: Corrected XPath syntax.
                # Do NOT concatenate CSS selector with XPath directly like before.
                # Instead, find any div or li elements *within the dialog role*,
                # which are common containers for individual user items.
                user_list_items_xpath = "//div[@role='dialog']//div[./div/a[contains(@href, '/') and @role='link']] | //div[@role='dialog']//li"
                
                user_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, user_list_items_xpath))
                )

                if not user_elements:
                    print("    ⚠️ No user list items found to scroll to. Breaking scroll loop.")
                    break
                
                # Get the last visible user element
                last_user_element = user_elements[-1]
                
                # Scroll the last user element into view using JavaScript
                # This explicitly makes the browser scroll to make the element visible
                driver.execute_script("arguments[0].scrollIntoView(true);", last_user_element)
                
                # Add a slightly longer, more random delay for content to load after scroll
                time.sleep(random.uniform(5, 9))

                # Re-fetch usernames after scrolling
                current_visible_usernames = get_usernames_from_popup(driver)
                new_users_added = len(set(current_visible_usernames) - all_collected_usernames)
                all_collected_usernames.update(current_visible_usernames)
                
                if len(all_collected_usernames) == last_known_username_count:
                    stagnation_count += 1
                    print(f"    ⚠️ No new usernames detected. Stagnation count: {stagnation_count}")
                    if stagnation_count >= 3: # Allow 3 attempts for new content
                        print("    🛑 Stagnation detected: No new usernames loaded after 3 attempts. Stopping scrolling.")
                        break
                else:
                    stagnation_count = 0 # Reset stagnation if new users were found
                    last_known_username_count = len(all_collected_usernames)
                
                scroll_count += 1
                print(f"    Scroll attempt {scroll_count}/{SCROLL_ATTEMPTS_MAX}. Found {new_users_added} new usernames. Total unique collected: {len(all_collected_usernames)}")
                
            except StaleElementReferenceException:
                print("    ⚠️ Stale Element: User list items became stale. Attempting to re-locate.")
                stagnation_count += 1 # Treat as a form of stagnation, as content isn't stable
                if stagnation_count >= 3:
                    print("    🛑 Stagnation detected due to repeated stale elements. Stopping scrolling.")
                    break
                time.sleep(random.uniform(2, 4)) # Small pause before re-attempt
                continue # Continue to the next iteration to re-find elements
            except TimeoutException:
                print("    ❌ Timeout: No user list items found within 10 seconds during scroll attempt. Stopping scrolling.")
                break
            except Exception as e:
                print(f"    ❌ Error during element-based scrolling: {e}. Stopping scrolling.")
                break

        print(f"✅ Finished scrolling popup. Total scrolls performed: {scroll_count}. "
              f"Final total unique usernames collected: {len(all_collected_usernames)}")

    except TimeoutException:
        print("❌ Timeout: Followers/Following pop-up scrollable area not found within 15 seconds. Check selector.")
    except Exception as e:
        print(f"❌ Error during initial pop-up setup: {e}")

def get_usernames_from_popup(driver):
    """
    Extracts visible usernames from the followers or following pop-up.
    This function has been enhanced to be more robust, checking aria-label
    and improving href parsing to pick up more usernames if they appear on screen.
    """
    usernames = set()
    try:
        # Looking for all 'a' tags within the dialog, which are typically used for profile links.
        # This is a broad search for any clickable link within the dialog.
        all_potential_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//a"))
        )

        for element in all_potential_elements:
            try:
                # 1. Try to extract username from 'aria-label' attribute (very reliable for Instagram)
                aria_label = element.get_attribute("aria-label")
                if aria_label:
                    # Example: "Profile picture of username" or "username"
                    # Prioritize exact username match if aria_label is simple
                    if ' ' not in aria_label and re.match(r"^[a-zA-Z0-9_.]+$", aria_label):
                        usernames.add(aria_label)
                        continue # Found a username, move to the next element
                    # If it's a "Profile picture of..." label
                    username_match_label = re.search(r'profile picture of (.+)', aria_label.lower())
                    if username_match_label:
                        username = username_match_label.group(1).strip()
                        if username and username.lower() not in ["null", "profile picture of"]: # Filter out non-real names
                            if re.match(r"^[a-zA-Z0-9_.]+$", username): # Validate format
                                usernames.add(username)
                                continue # Found a username, move to the next element

                # 2. If not found via aria-label, try to extract username from 'href' attribute
                href = element.get_attribute("href")
                if href:
                    # Filter out non-profile links by common patterns
                    # These are specific Instagram internal paths that are not user profiles
                    if any(filter_part in href for filter_part in ["/p/", "/explore/tags/", "/direct/", "/stories/", "/reels/", "/accounts/", "/legal/", "/about/", "/emails/", "/challenge/"]):
                        continue # Skip this href as it's not a profile link

                    # Attempt to extract the last part of the URL path as a potential username
                    # Handle both full URLs (https://www.instagram.com/user/) and relative paths (/user/)
                    parts = href.strip('/').split('/')
                    username_candidate = None

                    # Iterate from the end to find the last non-empty, non-domain part
                    for part in reversed(parts):
                        if part and part.lower() not in ["www.instagram.com", "instagram.com"]:
                            username_candidate = part
                            break
                    
                    if username_candidate:
                        # Validate the extracted candidate looks like an Instagram username
                        # Instagram usernames consist of alphanumeric characters, periods, and underscores.
                        if re.match(r"^[a-zA-Z0-9_.]+$", username_candidate):
                            if username_candidate.lower() not in ["null", "accounts"]: # Additional common non-username words
                                usernames.add(username_candidate)

            except StaleElementReferenceException:
                # This can happen if the DOM changes during iteration (e.g., more scrolling)
                # print("        (Debug) Stale element encountered during username extraction. Skipping.") # Removed verbose debug
                continue # Just skip this element and try the next one
            except Exception as e:
                # Catch any other unexpected errors during processing a single single element
                # print(f"        (Debug) Error processing element for username: {e}") # Removed verbose debug
                continue # Skip this element

        return list(usernames)

    except TimeoutException:
        # This means no 'a' tags were found in the dialog within the timeout.
        # print("        (Debug) Timeout: No 'a' tags found in dialog for username extraction.") # Removed verbose debug
        pass # Just return empty list if no elements found
    except Exception as e:
        print(f"❌ Failed to extract usernames from pop-up: {e}")
    return [] # Ensure an empty list is returned on failure

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
def scrape_followers_and_following(driver, seed_usernames, process_and_live_export_profile_func, scrape_profiles_function, config_from_main, current_depth, scraped_usernames_set):
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
        scraped_usernames_set (set): A set of all usernames already *fully processed and exported*
                                     across all recursion depths. This set is managed by the initial caller
                                     and updated by `process_and_live_export_profile_func`.
    Returns:
        None: This function now handles live export internally and does not return a list.
    """
    
    # RECURSION_DEPTH is a global variable in this file, read from its own config load.
    if current_depth > RECURSION_DEPTH:
        print(f"Max recursion depth ({RECURSION_DEPTH}) reached. Stopping.")
        return # No return value, as we're live exporting

    print(f"\n✨ Entering recursion depth: {current_depth} for {len(seed_usernames)} seed(s).")

    # This set will hold usernames that are relevant AND NEWLY FOUND for the next recursion depth
    next_level_seed_usernames = set()

    for username in seed_usernames:
        print(f"    Processing followers/following for @{username} (Depth: {current_depth})")

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        # --- FIX START ---
        # Changed behavior for TimeoutException: now it warns but proceeds
        # General Exception still causes a skip for the current user.
        profile_page_loaded_successfully = False
        try:
            # Wait for the main profile header to load before trying to find buttons
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//header//h2")))
            print(f"    Profile page for {username} loaded.")
            profile_page_loaded_successfully = True
        except TimeoutException:
            # This is the specific change: Print warning, but DO NOT 'continue'.
            # This allows the code to proceed and try clicking the follower/following buttons,
            # as sometimes the header might not appear but the buttons are still interactive.
            print(f"    ⚠️ Warning: Profile page for {username} header did not load in time. Attempting to proceed with button clicks anyway.")
            profile_page_loaded_successfully = False # Mark as not fully loaded, but proceed
        except Exception as e:
            # For more critical errors that prevent any interaction with the profile, skip the user.
            print(f"    ❌ Critical Error loading profile page for {username}: {e}. Skipping this user for current depth's button clicks.")
            continue # Skip to the next seed_username if there's a fundamental issue with the profile page.
        # --- FIX END ---


        # --- STEP 2: Scrape Followers ---
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
                print("        Trying fallback XPath for followers button...")
                followers_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, followers_button_xpath_fallback))
                )

            driver.execute_script("arguments[0].click();", followers_button)
            print(f"    Clicked followers button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            # Call scroll_followers_popup to scroll using element-based method
            scroll_followers_popup(driver, scroll_attempts=SCROLL_ATTEMPTS_MAX) 

            # After scrolling is done, get the final list of unique usernames from the popup
            followers_list = get_usernames_from_popup(driver)
            print(f"    Collected {len(followers_list)} followers for {username} after fixed scrolls.")

            # Filter and live-export profiles
            processed_count_this_section = 0
            for follower_username in followers_list:
                if processed_count_this_section >= FOLLOWER_LIMIT:
                    print(f"    Reached FOLLOWER_LIMIT ({FOLLOWER_LIMIT}) for profiles from this section.")
                    break

                # Only perform light scrape and export if not already in the global scraped_usernames_set
                # This prevents redundant work and duplicate exports.
                if follower_username not in scraped_usernames_set:
                    relevant_profile_data = light_scrape_and_filter_profile(driver, follower_username, config_from_main) # Pass config_from_main for keywords
                    if relevant_profile_data:
                        # Perform live export for this relevant profile.
                        # The process_and_live_export_profile_func is responsible for adding
                        # the profile's username to the scraped_usernames_set.
                        process_and_live_export_profile_func(relevant_profile_data, config_from_main, scraped_usernames_set)
                        next_level_seed_usernames.add(follower_username) # Add to next recursion seeds

                processed_count_this_section += 1 
            followers_scraped_successfully = True 

        except TimeoutException as e:
            print(f"    ⚠️ Timeout: Followers button not found/clickable or pop-up not visible for {username}. Error: {e}")
        except NoSuchElementException as e:
            print(f"    ⚠️ Element not found: Followers button or pop-up element for {username}. Error: {e}")
        except Exception as e:
            print(f"    ❌ Error scraping followers for {username}: {e}")
        finally:
            if followers_scraped_successfully: 
                close_popup(driver)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX)) 


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
                print("        Trying fallback XPath for following button...")
                following_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, following_button_xpath_fallback))
                )

            driver.execute_script("arguments[0].click();", following_button)
            print(f"    Clicked following button for {username}.")
            time.sleep(random.uniform(3, 6)) # Allow pop-up to load

            # Call scroll_followers_popup to scroll using element-based method
            scroll_followers_popup(driver, scroll_attempts=SCROLL_ATTEMPTS_MAX) 

            # After scrolling is done, get the final list of unique usernames from the popup
            following_list = get_usernames_from_popup(driver)
            print(f"    Collected {len(following_list)} following for {username} after fixed scrolls.")

            # Filter and live-export profiles
            processed_count_this_section = 0
            for following_username in following_list:
                if processed_count_this_section >= FOLLOWER_LIMIT:
                    print(f"    Reached FOLLOWER_LIMIT ({FOLLOWER_LIMIT}) for profiles from this section.")
                    break

                # Only perform light scrape and export if not already in the global scraped_usernames_set
                if following_username not in scraped_usernames_set:
                    relevant_profile_data = light_scrape_and_filter_profile(driver, following_username, config_from_main) # Pass config_from_main
                    if relevant_profile_data:
                        # Perform live export for this relevant profile
                        # The process_and_live_export_profile_func is responsible for adding
                        # the profile's username to the scraped_usernames_set.
                        process_and_live_export_profile_func(relevant_profile_data, config_from_main, scraped_usernames_set)
                        next_level_seed_usernames.add(following_username) # Add to next recursion seeds

                processed_count_this_section += 1 
            following_scraped_successfully = True 

        except TimeoutException as e:
            print(f"    ⚠️ Timeout: Following button not found/clickable or pop-up not visible for {username}. Error: {e}")
        except NoSuchElementException as e:
            print(f"    ⚠️ Element not found: Following button or pop-up element for {username}. Error: {e}")
        except Exception as e:
            print(f"    ❌ Error scraping following for {username}: {e}")
        finally:
            if following_scraped_successfully: 
                close_popup(driver)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX)) 


    # Recursion: Scrape followers of newly found relevant profiles
    if next_level_seed_usernames and current_depth < RECURSION_DEPTH:
        print(f"\n    Recursion: Scraping followers of {len(next_level_seed_usernames)} newly found relevant profiles (Depth: {current_depth + 1})...")

        # Pass the accumulated scraped_usernames_set to the next recursion level.
        # This set is continuously updated by `process_and_live_export_profile_func`.
        scrape_followers_and_following(
            driver,
            list(next_level_seed_usernames), 
            process_and_live_export_profile_func, 
            scrape_profiles_function,
            config_from_main, 
            current_depth + 1,
            scraped_usernames_set # Pass the same, *mutated* set
        )

    return