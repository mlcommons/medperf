from selenium.webdriver.common.by import By

from ..base_page import BasePage


class BenchmarkDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='benchmark-header']")
    SUB_HEADER_1 = (By.CSS_SELECTOR, "[data-testid='benchmark-details-heading']")
    SUB_HEADER_2 = (By.CSS_SELECTOR, "[data-testid='benchmark-policy-heading']")

    STATE = (By.CSS_SELECTOR, "[data-testid='benchmark-state']")
    VALID = (By.CSS_SELECTOR, "[data-testid='benchmark-validity']")

    ID_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-id-label']")
    ID = (By.CSS_SELECTOR, "[data-testid='benchmark-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-owner-label']")
    OWNER = (By.CSS_SELECTOR, "[data-testid='benchmark-owner']")

    DESCRIPTION_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-description-label']")
    DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='benchmark-description']")
    DOCUMENTATION_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-documentation-label']")
    DOCUMENTATION = (By.CSS_SELECTOR, "[data-testid='benchmark-documentation-link']")
    NO_DOCUMENTATION = (By.CSS_SELECTOR, "[data-testid='benchmark-documentation-na']")
    REF_DATASET_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-dataset-label']")
    REF_DATASET = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-dataset-link']")

    DATA_PREP_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-data-prep-label']")
    DATA_PREP = (By.CSS_SELECTOR, "[data-testid='benchmark-data-prep-section'] [data-testid='container-link']")
    DATA_PREP_DATE = (By.CSS_SELECTOR, "[data-testid='benchmark-data-prep-section'] [data-testid='container-link-date']")
    DATA_PREP_STATE = (By.CSS_SELECTOR, "[data-testid='benchmark-data-prep-section'] [data-testid='container-link-state']")

    REF_MODEL_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-model-label']")
    REF_MODEL = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-model-section'] [data-testid='model-link']")
    REF_MODEL_DATE = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-model-section'] [data-testid='model-link-date']")
    REF_MODEL_STATE = (By.CSS_SELECTOR, "[data-testid='benchmark-ref-model-section'] [data-testid='model-link-state']")

    METRICS_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-metrics-label']")
    METRICS = (By.CSS_SELECTOR, "[data-testid='benchmark-metrics-section'] [data-testid='container-link']")
    METRICS_DATE = (By.CSS_SELECTOR, "[data-testid='benchmark-metrics-section'] [data-testid='container-link-date']")
    METRICS_STATE = (By.CSS_SELECTOR, "[data-testid='benchmark-metrics-section'] [data-testid='container-link-state']")

    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='benchmark-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='benchmark-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='benchmark-modified']")

    POLICY_FORM = (By.ID, "association-policy-form")
    DATASET_AUTO_APPROVE_LABEL = (
        By.CSS_SELECTOR,
        "label[for='dataset-auto-approve-mode']",
    )
    DATASET_AUTO_APPROVE = (By.ID, "dataset-auto-approve-mode")
    DATASET_ALLOW_LIST_CONTAINER = (By.ID, "dataset-allow-list-container")
    DATASET_ALLOW_LIST_EMAILS = (By.ID, "dataset-allow-list-emails")
    DATASET_ALLOW_LIST_LABEL = (
        By.CSS_SELECTOR,
        "label[for='dataset-allow-list-text-input']",
    )
    DATASET_ALLOW_LIST = (By.ID, "dataset-allow-list-text-input")
    MODEL_AUTO_APPROVE_LABEL = (
        By.CSS_SELECTOR,
        "label[for='model-auto-approve-mode']",
    )
    MODEL_AUTO_APPROVE = (By.ID, "model-auto-approve-mode")
    MODEL_ALLOW_LIST_CONTAINER = (By.ID, "model-allow-list-container")
    MODEL_ALLOW_LIST_EMAILS = (By.ID, "model-allow-list-emails")
    MODEL_ALLOW_LIST_LABEL = (
        By.CSS_SELECTOR,
        "label[for='model-allow-list-text-input']",
    )
    MODEL_ALLOW_LIST = (By.ID, "model-allow-list-text-input")
    EMAIL_CHIP = (By.CSS_SELECTOR, ".email-chip")
    REMOVE_EMAIL = (By.CSS_SELECTOR, ".remove-btn")
    SAVE = (By.ID, "save-policy-btn")

    DATASETS_ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='datasets-associations-btn']",
    )
    DATASETS_TITLE = DATASETS_ASSOCIATIONS_BTN
    DATASETS_ASSOCIATIONS = (By.ID, "datasets-associations")
    DATASETS_ASSOCS_COUNT = (
        By.CSS_SELECTOR,
        "button[data-testid='datasets-associations-btn'] h3 span.rounded-full.text-sm.font-bold",
    )
    DATASETS_PENDING_ASSOCS = (
        By.XPATH,
        "//button[@data-testid='datasets-associations-btn']//span[contains(normalize-space(.), 'pending associations')]",
    )
    DATASETS_ASSOCIATIONS_CARDS = (
        By.CSS_SELECTOR,
        "#datasets-associations [data-testid='associated-benchmark-item']",
    )

    MODELS_ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='models-associations-btn']",
    )
    MODELS_TITLE = MODELS_ASSOCIATIONS_BTN
    MODELS_ASSOCIATIONS = (By.ID, "models-associations")
    MODELS_ASSOCS_COUNT = (
        By.CSS_SELECTOR,
        "button[data-testid='models-associations-btn'] h3 span.rounded-full.text-sm.font-bold",
    )
    MODELS_PENDING_ASSOCS = (
        By.XPATH,
        "//button[@data-testid='models-associations-btn']//span[contains(normalize-space(.), 'pending associations')]",
    )
    MODELS_ASSOCIATIONS_CARDS = (
        By.CSS_SELECTOR,
        "#models-associations [data-testid='associated-benchmark-item']",
    )

    RESULTS_BTN = (By.CSS_SELECTOR, "button[data-testid='benchmark-results-btn']")
    RESULTS_TITLE = RESULTS_BTN
    RESULTS = (By.ID, "benchmark-results")
    RESULTS_COUNT = (
        By.CSS_SELECTOR,
        "button[data-testid='benchmark-results-btn'] h3 span.rounded-full.text-sm.font-bold",
    )
    RESULTS_CARDS = (By.CSS_SELECTOR, "#benchmark-results > div[data-testid]")
    ASSOCIATIONS_RESULTS_CONTAINER = (By.CSS_SELECTOR, "div.space-y-4")

    RESULT_MODAL = (By.ID, "page-modal")
    CLOSE_BTN = (By.CSS_SELECTOR, "#page-modal-footer button.close-modal-btn")
    RESULT_BTN = (By.CLASS_NAME, "view-result-btn")

    ASSOC_ANCHOR = (By.CSS_SELECTOR, "h3 a")
    ASSOC_NAME = ASSOC_ANCHOR
    ASSOC_APPROVAL_LABEL = (
        By.XPATH,
        ".//p[.//strong[contains(normalize-space(.), 'Approval Status')]]//strong",
    )
    ASSOC_APPROVAL = (
        By.XPATH,
        ".//p[.//strong[contains(normalize-space(.), 'Approval Status')]]//span[contains(@class,'rounded-full')]",
    )
    ASSOC_APPROVED_AT_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Approved')]]/strong",
    )
    ASSOC_APPROVED_AT = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Approved')]]//span",
    )
    ASSOC_MODIFIED_AT_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Modified')]]/strong",
    )
    ASSOC_MODIFIED_AT = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Modified')]]//span[@data-date]",
    )
    ASSOC_INITIATED_BY_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Initiated By')]]/strong",
    )
    ASSOC_INITIATED_BY = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Initiated By')]]",
    )
    ASSOC_REJECT = (By.XPATH, ".//form[contains(@action, '/benchmarks/reject')]//button")
    ASSOC_APPROVE = (By.XPATH, ".//form[contains(@action, '/benchmarks/approve')]//button")

    RESULT_NAME = (By.CSS_SELECTOR, "h3")
    RESULT_OWNER_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Data Owner')]]/strong",
    )
    RESULT_OWNER = (By.XPATH, ".//p[strong[contains(normalize-space(.), 'Data Owner')]]")
    RESULT_MODEL_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Model')]]/strong",
    )
    RESULT_MODEL = (By.XPATH, ".//p[strong[contains(normalize-space(.), 'Model')]]/a")
    RESULT_DATASET_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Dataset')]]/strong",
    )
    RESULT_DATASET = (By.XPATH, ".//p[strong[contains(normalize-space(.), 'Dataset')]]/a")
    RESULT_INFERENCE_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Inference Status')]]/strong",
    )
    RESULT_INFERENCE = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Inference Status')]]",
    )
    RESULT_METRICS_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Metrics Status')]]/strong",
    )
    RESULT_METRICS = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Metrics Status')]]",
    )
    RESULT_MODIFIED_LABEL = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Modified')]]/strong",
    )
    RESULT_MODIFIED = (
        By.XPATH,
        ".//p[strong[contains(normalize-space(.), 'Modified')]]//span[@data-date]",
    )
    RESULT_VIEW = (By.CSS_SELECTOR, ".view-result-btn")
    RESULT_NOT_SUBMITTED = (
        By.XPATH,
        ".//p[contains(normalize-space(.), 'Results not submitted')]",
    )

    def __init__(self, driver, benchmark="", entity_name=""):
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
