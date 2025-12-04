from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegBenchmarkPage(BasePage):
    REG_BMK_BTN = (By.CSS_SELECTOR, '[data-testid="reg-bmk-btn"]')
    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    REF_DATASET = (By.ID, "reference-dataset-tarball-url")
    DATA_PREP = (By.ID, "data-preparation-container")
    REF_MODEL = (By.ID, "reference-model-container")
    METRICS = (By.ID, "evaluator-container")
    REGISTER = (By.ID, "register-benchmark-btn")

    def register_benchmark(
        self,
        name,
        description,
        reference_dataset,
        data_preparator,
        reference_model,
        metrics,
    ):
        self.type(self.NAME, name)
        self.type(self.DESCRIPTION, description)
        self.type(self.REF_DATASET, reference_dataset)

        self.select_by_text(self.DATA_PREP, data_preparator)
        self.select_by_text(self.REF_MODEL, reference_model)
        self.select_by_text(self.METRICS, metrics)

        self.click(self.REGISTER)
