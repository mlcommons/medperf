from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegContainerPage(BasePage):
    REG_CONTAINER_BTN = (By.CSS_SELECTOR, '[data-testid="reg-cont-btn"]')

    FORM = (By.ID, "register-container-form")
    HEADER = (By.CSS_SELECTOR, "[data-testid='container-register-header']")

    NAME = (By.ID, "name")
    MANIFEST = (By.ID, "container-file")
    CONFIG = MANIFEST
    PARAMETERS = (By.ID, "parameters-file")
    ADDITIONAL = (By.ID, "additional-file")
    ENCRYPTED = (By.ID, "with-encryption")
    NOT_ENCRYPTED = (By.ID, "without-encryption")
    DECRYPTION_KEY = (By.ID, "decryption-file")
    REGISTER = (By.ID, "register-container-btn")

    NAME_LABEL = (By.CSS_SELECTOR, "[data-testid='container-name-label']")
    MANIFEST_LABEL = (By.CSS_SELECTOR, "[data-testid='container-manifest-label']")
    PARAMETERS_LABEL = (By.CSS_SELECTOR, "[data-testid='container-parameters-label']")
    ADDITIONAL_LABEL = (By.CSS_SELECTOR, "[data-testid='container-additional-label']")

    NAME_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='container-name-tooltip']")
    MANIFEST_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='container-manifest-tooltip']")
    PARAMETERS_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='container-parameters-tooltip']",
    )
    ADDITIONAL_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='container-additional-tooltip']",
    )

    RESUME_SCRIPT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#register-container-form\")')]",
    )

    def register_container(self, container, decryption_key="", mode="evaluation"):
        if isinstance(container, dict):
            name = container.get("name", "")
            config = container.get("config") or container.get("manifest") or ""
            parameters = (
                container.get("parameters") or container.get("parameters_file") or ""
            )
            additional = (
                container.get("additional_remote")
                or container.get("additional")
                or container.get("additional_file")
                or ""
            )
        else:
            name = container.name
            config = container.config
            parameters = container.parameters
            additional = container.additional_remote

        self.type(self.NAME, name)
        self.type(self.CONFIG, config)
        self.type(self.PARAMETERS, parameters)
        self.type(self.ADDITIONAL, additional)

        if mode == "evaluation":
            if decryption_key:
                self.click(self.ENCRYPTED)
                self.type(self.DECRYPTION_KEY, decryption_key)
            else:
                self.click(self.NOT_ENCRYPTED)

        self.click(self.REGISTER)
