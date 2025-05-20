import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class FollowersScraper:
    def __init__(self, driver, config):
        self.driver = driver
        self.limit = config.get("scrape_limit", 500)
        self.delay_seconds = config.get("delay_seconds", 2)

    def scrape_followers(self, username):
        return self._scrape_list(username, list_type="followers")

    def scrape_following(self, username):
        return self._scrape_list(username, list_type="following")

    def _scrape_list(self, username, list_type="followers"):
        profile_url = f"https://www.instagram.com/{username}/"
        self.driver.get(profile_url)
        time.sleep(self.delay_seconds)

        try:
            # Wait until followers/following count link is clickable
            wait = WebDriverWait(self.driver, 10)
            # Use xpath to get either followers or following link depending on list_type
            if list_type == "followers":
                link_xpath = "//a[contains(@href, '/followers')]"
            else:
                link_xpath = "//a[contains(@href, '/following')]"
            link = wait.until(EC.element_to_be_clickable((By.XPATH, link_xpath)))

            link.click()
            time.sleep(self.delay_seconds)

            scroll_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//ul")))
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            print(f"Could not open {list_type} list for {username}: {str(e)}")
            return []

        followers_set = set()
        prev_height = -1
        same_height_count = 0

        while len(followers_set) < self.limit:
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
            time.sleep(self.delay_seconds)

            # Extract usernames from the scroll box
            user_links = scroll_box.find_elements(By.TAG_NAME, "a")
            for link_elem in user_links:
                href = link_elem.get_attribute("href")
                if href:
                    parts = href.strip('/').split('/')
                    if len(parts) >= 1:
                        user = parts[-1]
                        if user and user not in followers_set and user != username:
                            followers_set.add(user)

            # Check if scroll height changed to stop scrolling if end reached
            current_height = self.driver.execute_script("return arguments[0].scrollTop", scroll_box)
            if current_height == prev_height:
                same_height_count += 1
                if same_height_count >= 3:  # Allow a few attempts
                    break
            else:
                same_height_count = 0
                prev_height = current_height

        # Close the modal by pressing ESC or clicking outside (optional)
        try:
            close_button = self.driver.find_element(By.XPATH, "//div[@role='dialog']//button")
            close_button.click()
        except Exception:
            pass  # Ignore if close button not found

        return list(followers_set)[:self.limit]
