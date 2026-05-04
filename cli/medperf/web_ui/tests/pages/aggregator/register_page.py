from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegAggregatorPage(BasePage):
    FORM = (By.ID, "aggregator-register-form")
    HEADER = (By.CSS_SELECTOR, "[data-testid='aggregator-register-header']")

    NAME_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-register-name-label']")
    ADDRESS_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-register-address-label']")
    PORT_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-register-port-label']")
    ADMIN_PORT_LABEL = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-register-admin-port-label']",
    )
    CONTAINER_LABEL = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-register-container-label']",
    )

    NAME = (By.ID, "name")
    ADDRESS = (By.ID, "address")
    PORT = (By.ID, "port")
    ADMIN_PORT = (By.ID, "admin-port")
    AGGREGATION_MLCUBE = (By.ID, "aggregation-mlcube")
    REGISTER = (By.ID, "register-aggregator-btn")
    NAME_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='aggregator-register-name-tooltip']")
    ADDRESS_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-register-address-tooltip']",
    )
    PORT_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='aggregator-register-port-tooltip']")
    ADMIN_PORT_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-register-admin-port-tooltip']",
    )
    CONTAINER_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-register-container-tooltip']",
    )
    RESUME_SCRIPT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#register-aggregator-form\")')]",
    )

    def register_aggregator(self, name, address, port, admin_port, aggregation_mlcube):
        self.type(self.NAME, name)
        self.type(self.ADDRESS, address)
        self.type(self.PORT, str(port))
        self.type(self.ADMIN_PORT, str(admin_port))
        self.select_by_text(self.AGGREGATION_MLCUBE, aggregation_mlcube)
        self.click(self.REGISTER)
