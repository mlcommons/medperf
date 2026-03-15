from selenium.webdriver.common.by import By
from ..base_page import BasePage


class BenchmarkDetailsPage(BasePage):
    DATASETS_ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='datasets-associations-btn']",
    )
    DATASETS_ASSOCIATIONS = (By.ID, "datasets-associations")

    MODELS_ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='models-associations-btn']",
    )
    MODELS_ASSOCIATIONS = (By.ID, "models-associations")

    RESULTS_BTN = (By.CSS_SELECTOR, "button[data-testid='benchmark-results-btn']")
    RESULTS = (By.ID, "benchmark-results")

    RESULT_MODAL = (By.ID, "page-modal")
    # New design: result modal uses page-modal, footer has button.close-modal-btn
    CLOSE_BTN = (By.CSS_SELECTOR, "#page-modal-footer button.close-modal-btn")

    RESULT_BTN = (By.CLASS_NAME, "view-result-btn")

    def __init__(self, driver, benchmark, entity_name=""):
        super().__init__(driver)
        self.BMK_BTN = (
            By.XPATH,
            f'//a[@data-testid="bmk-name" and contains(text(), "{benchmark}")]',
        )
        self.APPROVE_BTN = (
            By.XPATH,
            f'//div[@data-testid="associated-benchmark-item"][.//a[contains(normalize-space(.), "{entity_name}")]]'
            '//form[contains(@action,"/benchmarks/approve")]//button[normalize-space(text())="Approve"]',
        )

    def approve_dataset(self):
        self.click(self.DATASETS_ASSOCIATIONS_BTN)
        associations = self.find(self.DATASETS_ASSOCIATIONS)
        self.wait_for_visibility_element(associations)
        self.click(self.APPROVE_BTN)

    def approve_container(self):
        self.click(self.MODELS_ASSOCIATIONS_BTN)
        associations = self.find(self.MODELS_ASSOCIATIONS)
        self.wait_for_visibility_element(associations)
        self.click(self.APPROVE_BTN)

    def __view_result(self, result_btn):
        self.ensure_element_ready(result_btn)
        result_btn.click()
        view_modal = self.find(self.PAGE_MODAL)
        self.wait_for_visibility_element(view_modal)
        view_modal.find_element(*self.CLOSE_BTN).click()
        self.wait_for_invisibility_element(view_modal)

    def view_results(self):
        self.click(self.RESULTS_BTN)
        associations = self.find(self.RESULTS)
        self.wait_for_visibility_element(associations)
        for result_btn in associations.find_elements(*self.RESULT_BTN):
            self.__view_result(result_btn)
            self.click(self.RESULTS_BTN)
