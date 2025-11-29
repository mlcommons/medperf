from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import argparse
import os


def execute_browser_flow(email, password, url):
    confirm_btn_selector = (By.CSS_SELECTOR, "button[type='submit'][value='confirm']")
    email_field_selector = (By.ID, "username")
    continue_btn_selector = (By.CSS_SELECTOR, "button[type='submit'][value='default']")
    password_field_selector = (By.ID, "password")
    success_checkmark = (By.CSS_SELECTOR, "span.success-lock")

    options = Options()
    options.add_argument("--headless=true")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    driver.get(url)

    # Confirm device code
    confirm = wait.until(EC.presence_of_element_located(confirm_btn_selector))
    wait.until(EC.element_to_be_clickable(confirm))
    confirm.click()

    # Enter email and click continue
    email_field = wait.until(EC.presence_of_element_located(email_field_selector))
    wait.until(EC.element_to_be_clickable(email_field))
    email_field.send_keys(email)

    continue_btn = wait.until(EC.presence_of_element_located(continue_btn_selector))
    wait.until(EC.element_to_be_clickable(continue_btn))
    continue_btn.click()

    # Enter password and click continue (login)
    password_field = wait.until(EC.presence_of_element_located(password_field_selector))
    wait.until(EC.element_to_be_clickable(password_field))
    password_field.send_keys(password)

    login_btn = wait.until(EC.presence_of_element_located(continue_btn_selector))
    wait.until(EC.element_to_be_clickable(login_btn))
    login_btn.click()

    # Wait for the success mark to appear
    wait.until(EC.presence_of_element_located(success_checkmark))

    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email")
    parser.add_argument("--url")

    args = parser.parse_args()

    # load password from the environment
    try:
        password = os.environ["MOCK_USERS_PASSWORD"]
    except KeyError:
        raise RuntimeError(
            "The environment variable `MOCK_USERS_PASSWORD` must be set."
        )

    execute_browser_flow(args.email, password, args.url)
