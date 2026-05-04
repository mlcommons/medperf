from selenium.webdriver.common.by import By
from .base_page import BasePage


class SecurityPage(BasePage):
    FORM = (By.ID, "security-check-form")
    HEADER = (By.CSS_SELECTOR, "h2.text-2xl")
    TITLE = HEADER
    TOKEN_LABEL = (By.CSS_SELECTOR, 'label[for="token"]')
    TOKEN = (By.ID, "token")
    SUBMIT = (By.ID, "security-check-btn")
    HELP_BTN = (By.ID, "show-help-modal")
    ERROR = (By.CSS_SELECTOR, "[role='alert']")

    def enter_token(self, token):
        self.type(self.TOKEN, token)
        self.click(self.SUBMIT)
