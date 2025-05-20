import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class ProfileScraper:
    def __init__(self, driver, config):
        self.driver = driver
        self.delay_seconds = config.get("delay_seconds", 2)

    def scrape_light_profile(self, username):
        """
        Scrape basic info: bio, full name, external link.
        Used for filtering.
        """
        profile_url = f"https://www.instagram.com/{username}/"
        self.driver.get(profile_url)
        time.sleep(self.delay_seconds)

        bio = self._get_text_by_xpath("//div[@class='-vDIg']/span") or ""
        full_name = self._get_text_by_xpath("//h1") or ""
        external_link = self._get_external_link()

        return {
            "username": username,
            "full_name": full_name,
            "bio": bio,
            "external_link": external_link
        }

    def scrape_full_profile(self, username):
        """
        Scrape full profile details for filtered usernames.
        Extract WhatsApp numbers and group links.
        """
        profile_data = self.scrape_light_profile(username)

        follower_count = self._get_follower_count()
        profile_url = f"https://www.instagram.com/{username}/"

        whatsapp_numbers = self._extract_whatsapp_numbers(profile_data["bio"])
        whatsapp_groups = self._extract_whatsapp_groups(profile_data["bio"])

        region = self._detect_region(whatsapp_numbers)

        profile_data.update({
            "follower_count": follower_count,
            "profile_url": profile_url,
            "whatsapp_numbers": whatsapp_numbers,
            "whatsapp_groups": whatsapp_groups,
            "region": region
        })

        return profile_data

    def search_and_scrape_profile(self, username):
        """
        Search Instagram for the username, click exact match, then scrape full profile.
        """
        try:
            # Wait for search box and clear it
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']"))
            )
            search_box.clear()
            time.sleep(0.5)
            search_box.send_keys(username)
            time.sleep(1.5)  # wait for search results

            # Grab search results links
            results = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@aria-label, 'Search results')]//a")
                )
            )

            matched_link = None
            for result in results:
                href = result.get_attribute("href")
                if href:
                    profile_username = href.rstrip('/').split('/')[-1]
                    if profile_username.lower() == username.lower():
                        matched_link = result
                        break

            if not matched_link:
                print(f"No exact match found for username '{username}'.")
                return None

            matched_link.click()
            time.sleep(self.delay_seconds)

            # Confirm page loaded with correct username (optional check)
            actual_username = self._get_text_by_xpath("//h2[contains(@class,'rhpdm')]") or \
                              self._get_text_by_xpath("//header//section//h2")
            if actual_username and actual_username.lower() != username.lower():
                print(f"Username mismatch after clicking: expected {username}, found {actual_username}")
                return None

            # Scrape full profile details now that we are on the page
            return self.scrape_full_profile(username)

        except TimeoutException:
            print(f"Timeout while searching for username '{username}'.")
            return None

    def _get_text_by_xpath(self, xpath):
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip()
        except NoSuchElementException:
            return None

    def _get_external_link(self):
        try:
            # Instagram external link is within <a> inside the bio section, usually
            link_elem = self.driver.find_element(By.XPATH, "//div[@class='-vDIg']//a[contains(@href, 'http')]")
            return link_elem.get_attribute("href")
        except NoSuchElementException:
            return None

    def _get_follower_count(self):
        try:
            followers_elem = self.driver.find_element(By.XPATH, "//ul/li[2]/a/span")
            count_text = followers_elem.get_attribute("title") or followers_elem.text
            return self._parse_count(count_text)
        except NoSuchElementException:
            return 0

    def _parse_count(self, count_str):
        count_str = count_str.replace(",", "").strip()
        try:
            if "k" in count_str.lower():
                return int(float(count_str.lower().replace("k", "")) * 1000)
            elif "m" in count_str.lower():
                return int(float(count_str.lower().replace("m", "")) * 1000000)
            else:
                return int(count_str)
        except ValueError:
            return 0

    def _extract_whatsapp_numbers(self, text):
        """
        Regex to extract WhatsApp numbers from bio text.
        Examples: +52 1234567890, wa.me/1234567890, Wsp 1234567890
        """
        if not text:
            return []

        patterns = [
            r"\+?\d{1,3}[\s-]?\d{6,14}",  # phone numbers with country code
            r"wa\.me\/(\d{6,14})",        # wa.me links
            r"Wsp[\s:]?(\d{6,14})",       # Wsp followed by number
        ]
        numbers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    number = match[0]
                else:
                    number = match
                numbers.add(number.strip())

        return list(numbers)

    def _extract_whatsapp_groups(self, text):
        """
        Extract WhatsApp group links from bio text.
        Format: chat.whatsapp.com/xxxx
        """
        if not text:
            return []

        pattern = r"(https?:\/\/)?chat\.whatsapp\.com\/[a-zA-Z0-9]+"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        groups = [match if match.startswith("http") else f"https://{match}" for match in matches]

        return groups

    def _detect_region(self, numbers):
        """
        Detect region based on country code prefix in WhatsApp numbers.
        Example: +52 = Mexico, +55 = Brazil, +54 = Argentina
        """
        region_map = {
            "+52": "Mexico",
            "+55": "Brazil",
            "+54": "Argentina",
            "+57": "Colombia",
            "+56": "Chile",
            "+58": "Venezuela",
            "+593": "Ecuador",
            "+51": "Peru",
            "+505": "Nicaragua",
            "+507": "Panama",
        }
        for number in numbers:
            for code, country in region_map.items():
                if number.startswith(code):
                    return country
        return "Unknown"
