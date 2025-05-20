# scrapers/login.py

import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginHandler:
    def __init__(self, driver, config):
        self.driver = driver
        creds = config.get("credentials", {}) if config else {}
        self.username = creds.get("username")
        self.password = creds.get("password")
        self.delay = config.get("delay_between_requests", 2) if config else 2

        if not self.username or not self.password:
            raise ValueError("Instagram username or password not found in config credentials.")

    def login(self):
        login_url = "https://www.instagram.com/accounts/login/"
        self.driver.get(login_url)
        time.sleep(self.delay)

        try:
            username_input = self.driver.find_element(By.NAME, "username")
            username_input.clear()
            username_input.send_keys(self.username)
            print("Entered username.")
        except NoSuchElementException:
            print("Username input not found.")
            return False

        try:
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            print("Entered password.")
        except NoSuchElementException:
            print("Password input not found.")
            return False

        try:
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            print("Clicked login button.")
        except NoSuchElementException:
            print("Login button not found.")
            return False

        # Wait a bit after clicking login for page load or 2FA prompt
        time.sleep(self.delay + 5)

        if self._is_2fa_required():
            if not self._handle_2fa():
                print("2FA failed or timed out.")
                return False

        print("Login process done. Proceeding with scraping.")
        return True

    def _is_2fa_required(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, "verificationCode"))
            )
            print("2FA required.")
            return True
        except TimeoutException:
            return False

    def _handle_2fa(self):
        try:
            code_input = self.driver.find_element(By.NAME, "verificationCode")
            code = input("Enter Instagram 2FA code: ").strip()
            code_input.send_keys(code)
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            print("Submitted 2FA code.")
            time.sleep(self.delay + 5)  # Wait for page to load after 2FA
            return True
        except NoSuchElementException:
            return False
