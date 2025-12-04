from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    TITLE = (By.CSS_SELECTOR, "h3.text-center")
    FORM = (By.ID, "medperf-login-form")
    EMAIL_LABEL = (By.CSS_SELECTOR, 'label[for="email"]')
    EMAIL = (By.ID, "email")
    LOGIN = (By.ID, "medperf-login-btn")
    NOT_LOGGED_IN_ALERT = (By.CSS_SELECTOR, "div.alert.alert-danger")
    CONFIRM_TEXT = (By.ID, "confirm-text")

    def login(self, email):
        self.type(self.EMAIL, email)
        self.click(self.LOGIN)
