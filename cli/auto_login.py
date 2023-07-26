from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import os


def execute_browser_flow(email, password, url):
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 30)
    driver.get(url)

    # Confirm device code

    continue_btn = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[name='action'][type='submit']")
        )
    )

    wait.until(EC.element_to_be_clickable(continue_btn))

    continue_btn.click()

    # Enter email and click continue

    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))

    wait.until(EC.element_to_be_clickable(email_field))

    email_field.send_keys(email)

    continue_btn = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "button[name='action'][type='submit'][data-action-button-primary='true']",
            )
        )
    )

    wait.until(EC.element_to_be_clickable(continue_btn))

    continue_btn.click()

    # Enter password and click continue (login)

    password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))

    wait.until(EC.element_to_be_clickable(password_field))

    password_field.send_keys(password)

    login_btn = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "button[name='action'][type='submit'][data-action-button-primary='true']",
            )
        )
    )

    wait.until(EC.element_to_be_clickable(login_btn))

    login_btn.click()

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
