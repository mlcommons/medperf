from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegContainerPage(BasePage):
    REG_CONTAINER_BTN = (By.CSS_SELECTOR, '[data-testid="reg-cont-btn"]')
    NAME = (By.ID, "name")
    CONFIG = (By.ID, "container-file")
    PARAMETERS = (By.ID, "parameters-file")
    ADDITIONAL = (By.ID, "additional-file")
    ENCRYPTED = (By.ID, "with-encryption")
    NOT_ENCRYPTED = (By.ID, "without-encryption")
    DECRYPTION_KEY = (By.ID, "decryption-file")
    REGISTER = (By.ID, "register-container-btn")

    def register_container(self, container, decryption_key=""):
        self.type(self.NAME, container.name)
        self.type(self.CONFIG, container.config)
        self.type(self.PARAMETERS, container.parameters)
        self.type(self.ADDITIONAL, container.additional_remote)

        if decryption_key:
            self.click(self.ENCRYPTED)
            self.type(self.DECRYPTION_KEY, decryption_key)
        else:
            self.click(self.NOT_ENCRYPTED)

        self.click(self.REGISTER)
