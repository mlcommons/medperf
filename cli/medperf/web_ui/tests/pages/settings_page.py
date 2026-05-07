from selenium.webdriver.common.by import By

from .base_page import BasePage


class SettingsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "h1.text-3xl")
    PROFILE_SECTION_HEADING = (
        By.XPATH,
        "//h2[contains(normalize-space(.), 'Profile Settings')]",
    )
    CERT_SECTION_HEADING = (
        By.XPATH,
        "//h2[contains(normalize-space(.), 'Certificate Settings')]",
    )

    CURRENT_PROFILE = (By.CSS_SELECTOR, 'strong[data-testid="current-profile"]')
    FORM = (By.ID, "profiles-form")
    PROFILE_LABEL = (By.CSS_SELECTOR, 'label[for="profile"]')
    PROFILE = (By.ID, "profile")
    ACTIVATE = (By.ID, "activate-profile-btn")
    VIEW_PROFILE = (By.ID, "view-profile-btn")

    EDIT_CONFIG_CONTAINER = (By.ID, "edit-config-container")
    EDIT_CONFIG_FORM = (By.ID, "edit-config-form")
    GPUS = (By.ID, "gpus")
    GPUS_LABEL = (By.CSS_SELECTOR, 'label[for="gpus"]')
    PLATFORM = (By.ID, "platform")
    PLATFORM_LABEL = (By.CSS_SELECTOR, 'label[for="platform"]')
    CA = (By.ID, "ca")
    CA_LABEL = (By.CSS_SELECTOR, 'label[for="ca"]')
    FINGERPRINT = (By.ID, "fingerprint")
    FINGERPRINT_LABEL = (By.CSS_SELECTOR, 'label[for="fingerprint"]')
    APPLY_CHANGES = (By.ID, "apply-profile-changes-btn")

    CERT_SETTINGS = (By.ID, "certificate-settings")
    GET_CERTIFICATE = (By.ID, "get-cert-btn")
    SUBMIT_CERTIFICATE = (By.ID, "submit-cert-btn")
    DELETE_CERTIFICATE = (By.ID, "delete-cert-btn")
    CERTIFICATE_STATUS = (By.CSS_SELECTOR, 'span[data-testid="cert-status"]')

    CC_OPERATOR_SECTION = (By.ID, "edit-cc-operator-container")
    CC_OPERATOR_FORM = (By.ID, "edit-cc-operator-form")
    CC_CONFIGURE_TOGGLE = (By.ID, "configure-cc-operator")
    CC_APPLY_BTN = (By.ID, "apply-cc-operator-btn")

    def activate_profile(self, profile_name):
        self.select_by_text(self.PROFILE, profile_name)
        self.click(self.ACTIVATE)

    def get_client_certificate(self):
        self.click(self.GET_CERTIFICATE)

    def submit_certificate(self):
        self.click(self.SUBMIT_CERTIFICATE)
