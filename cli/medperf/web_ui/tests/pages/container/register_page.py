from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegContainerPage(BasePage):
    REG_CONTAINER_BTN = (By.CSS_SELECTOR, '[data-testid="reg-cont-btn"]')
    NAME = (By.ID, "name")
    MANIFEST = (By.ID, "container-file")
    PARAMETERS = (By.ID, "parameters-file")
    ADDITIONAL = (By.ID, "additional-file")
    REGISTER = (By.ID, "register-container-btn")

    def register_container(self, container_dict):
        self.type(self.NAME, container_dict["name"])
        self.type(self.MANIFEST, container_dict["manifest"])
        if container_dict["parameters"]:
            self.type(self.PARAMETERS, container_dict["parameters"])
        if container_dict["additional"]:
            self.type(self.ADDITIONAL, container_dict["additional"])

        self.click(self.REGISTER)
