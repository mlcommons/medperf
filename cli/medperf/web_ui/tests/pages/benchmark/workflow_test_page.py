from selenium.webdriver.common.by import By
from ..base_page import BasePage


class WorkflowTestPage(BasePage):
    BMK_REG_BTN = (By.CSS_SELECTOR, '[data-testid="reg-bmk-btn"]')
    WF_BTN = (By.CSS_SELECTOR, 'a[href="/benchmarks/register/workflow_test"]')
    DATA_PREP = (By.ID, "data-preparation")
    MODEL = (By.ID, "model-path")
    EVALUATOR = (By.ID, "evaluator-path")
    DATA = (By.ID, "data-path")
    LABELS = (By.ID, "labels-path")
    RUN_TEST_BTN = (By.ID, "run-workflow-test-btn")
    CONTINUE_BTN = (By.CSS_SELECTOR, "button.btn-success")

    def run_test(
        self, data_prep_path, model_path, evaluator_path, data_path, labels_path
    ):
        self.type(self.DATA_PREP, data_prep_path)
        self.type(self.MODEL, model_path)
        self.type(self.EVALUATOR, evaluator_path)
        self.type(self.DATA, data_path)
        self.type(self.LABELS, labels_path)

        self.click(self.RUN_TEST_BTN)
