from selenium.webdriver.common.by import By
from .base_page import BasePage


class SettingsPage(BasePage):
    CURRENT_PROFILE = (By.CSS_SELECTOR, 'strong[data-testid="current-profile"]')
    FORM = (By.ID, "profiles-form")
    PROFILE_LABEL = (By.CSS_SELECTOR, 'label[for="profile"]')
    PROFILE = (By.ID, "profile")
    ACTIVATE = (By.ID, "activate-profile-btn")
    GET_CERTIFICATE = (By.ID, "get-cert-btn")
    SUBMIT_CERTIFICATE = (By.ID, "submit-cert-btn")
    CERTIFICATE_STATUS = (By.CSS_SELECTOR, 'span[data-testid="cert-status"]')

    def activate_profile(self, profile_name):
        self.select_by_text(self.PROFILE, profile_name)
        self.click(self.ACTIVATE)

    def get_client_certificate(self):
        self.click(self.GET_CERTIFICATE)

    def submit_certificate(self):
        self.click(self.SUBMIT_CERTIFICATE)
