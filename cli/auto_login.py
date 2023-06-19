from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import argparse


def execute_browser_flow(email, password, url):
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 30)
    driver.get(url)

    continue_btn = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[name='action'][type='submit']")
        )
    )

    wait.until(EC.element_to_be_clickable(continue_btn))

    continue_btn.click()

    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))

    wait.until(EC.element_to_be_clickable(email_field))
    wait.until(EC.element_to_be_clickable(password_field))

    email_field.send_keys(email)
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
    parser.add_argument("--password")
    parser.add_argument("--url")

    args = parser.parse_args()
    execute_browser_flow(args.email, args.password, args.url)
