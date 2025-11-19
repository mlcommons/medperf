from selenium.webdriver.common.by import By
from .base_page import BasePage


class SecurityPage(BasePage):
    FORM = (By.ID, "security-check-form")
    TITLE = (By.CSS_SELECTOR, ".card-body h2")
    TOKEN_LABEL = (By.CSS_SELECTOR, 'label[for="token"]')
    TOKEN = (By.ID, "token")
    SUBMIT = (By.ID, "security-check-btn")
    HELP_BTN = (By.CSS_SELECTOR, '[data-bs-target="#security-check-modal"]')
    HELP_MODAL = (By.ID, "security-check-modal")
    CLOSE_HELP = (By.CSS_SELECTOR, '[data-bs-dismiss="modal"]')
    ERROR = (By.CSS_SELECTOR, "div.alert.alert-danger[role='alert']")

    def enter_token(self, token):
        self.type(self.TOKEN, token)
        self.click(self.SUBMIT)
