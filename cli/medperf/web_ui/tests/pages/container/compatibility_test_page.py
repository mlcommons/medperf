from selenium.webdriver.common.by import By
from ..base_page import BasePage


class CompatibilityTestPage(BasePage):
    REG_CONT_BTN = (By.CSS_SELECTOR, '[data-testid="reg-cont-btn"]')
    COMP_BTN = (By.CSS_SELECTOR, 'a[href="/containers/register/compatibility_test"]')
    BENCHMARK = (By.ID, "benchmark")
    CONTAINER = (By.ID, "container-path")
    RUN_TEST_BTN = (By.ID, "run-comp-test-btn")
    CONTINUE_BTN = (By.CSS_SELECTOR, "button.btn-success")

    def run_test(self, benchmark, container_path):
        self.select_by_text(self.BENCHMARK, benchmark)
        self.type(self.CONTAINER, container_path)

        self.click(self.RUN_TEST_BTN)
