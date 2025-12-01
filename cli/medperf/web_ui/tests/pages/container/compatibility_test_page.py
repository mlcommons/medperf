from selenium.webdriver.common.by import By
from ..base_page import BasePage


class CompatibilityTestPage(BasePage):
    REG_CONT_BTN = (By.CSS_SELECTOR, '[data-testid="reg-cont-btn"]')
    COMP_BTN = (By.CSS_SELECTOR, 'a[href="/containers/register/compatibility_test"]')
    BENCHMARK = (By.ID, "benchmark")
    MODEL_CONFIG = (By.ID, "container-file")
    MODEL_PARAMETERS = (By.ID, "parameters-file")
    MODEL_ADDITIONAL = (By.ID, "additional-file")
    RUN_TEST_BTN = (By.ID, "run-comp-test-btn")
    CONTINUE_BTN = (By.CSS_SELECTOR, "button.btn-success")
    NOT_ENCRYPTED = (By.ID, "without-encryption")

    def run_test(self, benchmark, model):
        self.select_by_text(self.BENCHMARK, benchmark)
        self.type(self.MODEL_CONFIG, model.config)
        self.type(self.MODEL_PARAMETERS, model.parameters)
        self.type(self.MODEL_ADDITIONAL, model.additional_local)
        self.click(self.NOT_ENCRYPTED)

        self.click(self.RUN_TEST_BTN)
