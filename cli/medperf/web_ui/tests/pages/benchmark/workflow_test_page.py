from selenium.webdriver.common.by import By
from ..base_page import BasePage


class WorkflowTestPage(BasePage):
    BMK_REG_BTN = (By.CSS_SELECTOR, '[data-testid="reg-bmk-btn"]')
    WF_BTN = (By.CSS_SELECTOR, 'a[href="/benchmarks/register/workflow_test"]')
    DATA_PREP_CONFIG = (By.ID, "data-preparation")
    DATA_PREP_PARAMETERS = (By.ID, "data-preparation-parameters")
    DATA_PREP_ADDITIONAL = (By.ID, "data-preparation-additional")
    MODEL_CONFIG = (By.ID, "model-path")
    MODEL_PARAMETERS = (By.ID, "model-parameters-path")
    MODEL_ADDITIONAL = (By.ID, "model-additional-path")
    EVALUATOR_CONFIG = (By.ID, "evaluator-path")
    EVALUATOR_PARAMETERS = (By.ID, "evaluator-parameters-path")
    EVALUATOR_ADDITIONAL = (By.ID, "evaluator-additional-path")
    DATA = (By.ID, "data-path")
    LABELS = (By.ID, "labels-path")
    RUN_TEST_BTN = (By.ID, "run-workflow-test-btn")
    CONTINUE_BTN = (By.CSS_SELECTOR, "button.btn-success")

    def run_test(self, data_prep, ref_model, evaluator, data_path, labels_path):
        self.type(self.DATA_PREP_CONFIG, data_prep.config)
        self.type(self.DATA_PREP_PARAMETERS, data_prep.parameters)
        self.type(self.DATA_PREP_ADDITIONAL, data_prep.additional_local)
        self.type(self.MODEL_CONFIG, ref_model.config)
        self.type(self.MODEL_PARAMETERS, ref_model.parameters)
        self.type(self.MODEL_ADDITIONAL, ref_model.additional_local)
        self.type(self.EVALUATOR_CONFIG, evaluator.config)
        self.type(self.EVALUATOR_PARAMETERS, evaluator.parameters)
        self.type(self.EVALUATOR_ADDITIONAL, evaluator.additional_local)
        self.type(self.DATA, data_path)
        self.type(self.LABELS, labels_path)

        self.click(self.RUN_TEST_BTN)
