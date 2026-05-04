from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegBenchmarkPage(BasePage):
    REG_BMK_BTN = (By.CSS_SELECTOR, '[data-testid="reg-bmk-btn"]')

    FORM = (By.ID, "benchmark-register-form")
    HEADER = (By.CSS_SELECTOR, "[data-testid='benchmark-register-header']")

    REQUIRE_TESTS = (By.ID, "noskip-tests")
    SKIP_TESTS = (By.ID, "skip-tests")

    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    REF_DATASET = (By.ID, "reference-dataset-tarball-url")
    DATA_PREP = (By.ID, "data-preparation-container")
    REF_MODEL = (By.ID, "reference-model")
    METRICS = (By.ID, "evaluator-container")
    REGISTER = (By.ID, "register-benchmark-btn")

    ALREADY_PREPARED = (By.ID, "skip-dataprep")
    NOT_PREPARED = (By.ID, "noskip-dataprep")

    NAME_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-name-label']")
    DESCRIPTION_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-description-label']")
    REF_DATASET_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-dataset-label']")
    DATA_PREP_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-data-prep-label']")
    REF_MODEL_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-model-label']")
    METRICS_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-metrics-label']")

    ALREADY_PREPARED_LABEL = (By.XPATH, "//label[.//input[@id='skip-dataprep']]")
    NOT_PREPARED_LABEL = (By.XPATH, "//label[.//input[@id='noskip-dataprep']]")

    NAME_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='benchmark-name-tooltip']")
    DESCRIPTION_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='benchmark-description-tooltip']")
    REF_DATASET_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-dataset-tooltip']")

    RESUME_SCRIPT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#benchmark-register-form\")')]",
    )

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
