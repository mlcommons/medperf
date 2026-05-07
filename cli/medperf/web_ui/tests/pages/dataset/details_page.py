from selenium.webdriver.common.by import By

from ..base_page import BasePage


class DatasetDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='dataset-header']")
    SUB_HEADER_1 = (By.CSS_SELECTOR, "[data-testid='dataset-details-heading']")

    STATE = (By.CSS_SELECTOR, "[data-testid='dataset-state']")
    VALID = (By.CSS_SELECTOR, "[data-testid='dataset-validity']")

    ID_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-id-label']")
    ID = (By.CSS_SELECTOR, "[data-testid='dataset-id']")

    DATA_PREP_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-data-prep-label']")
    DATA_PREP = (
        By.CSS_SELECTOR,
        "[data-testid='dataset-data-prep-section'] [data-testid='container-link']",
    )
    DATA_PREP_DATE = (
        By.CSS_SELECTOR,
        "[data-testid='dataset-data-prep-section'] [data-testid='container-link-date']",
    )
    DATA_PREP_STATE = (
        By.CSS_SELECTOR,
        "[data-testid='dataset-data-prep-section'] [data-testid='container-link-state']",
    )

    PREPARED_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-prepared-label']")
    PREPARED = (By.CSS_SELECTOR, "[data-testid='dataset-prepared']")

    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-owner-label']")
    OWNER = (By.CSS_SELECTOR, "[data-testid='dataset-owner']")

    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='dataset-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='dataset-modified']")

    STATISTICS_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-statistics-label']")
    STATISTICS = (By.CSS_SELECTOR, "[data-testid='dataset-statistics-btn']")

    REPORT_LABEL = (By.CSS_SELECTOR, "[data-testid='dataset-report-label']")
    REPORT = (By.CSS_SELECTOR, "[data-testid='dataset-report-btn']")

    EXPORT_FORM = (By.ID, "redirect-export-form")
    EXPORT = (By.CSS_SELECTOR, '#redirect-export-form input[type="submit"]')

    BOTTOM_BUTTONS_CONTAINER = (
        By.XPATH,
        "//h3[contains(normalize-space(.), 'Actions')]",
    )

    PERPARE_NOTE = (
        By.XPATH,
        "//form[@id='prepare-dataset-form']/preceding-sibling::p[1]",
    )
    SET_OPERATIONAL_NOTE = (
        By.XPATH,
        "//p[contains(normalize-space(.), 'Complete preparation first.')]"
        "/preceding-sibling::p[1]",
    )
    ASSCOATE_NOTE = (
        By.XPATH,
        "//p[contains(normalize-space(.), 'Set dataset to operational first.')]"
        "/preceding-sibling::p[1]",
    )

    PREPARE_BTN = (By.ID, "prepare-dataset")
    PREPARED_TEXT = (
        By.CSS_SELECTOR,
        '[data-testid="prepared-section"] span.font-semibold',
    )

    SET_OPERATIONAL_BTN = (By.ID, "set-operational")
    SET_OPERATIONAL_TEXT = (
        By.CSS_SELECTOR,
        '[data-testid="operational-section"] span.font-semibold',
    )

    ACTION_GRID_CARDS = (
        By.XPATH,
        "//h3[normalize-space(.)='Actions']"
        "/ancestor::div[contains(@class,'rounded-2xl')][1]"
        "//div[contains(@class,'md:grid-cols-3')]"
        "/div[contains(@class,'rounded-xl')]",
    )

    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    DROPDOWN_CONTAINER = (By.ID, "dropdown-div")
    NO_BMKS = (
        By.XPATH,
        "//div[@id='dropdown-div']//p[contains(normalize-space(.), "
        "'No benchmarks available')]",
    )

    ASSOCIATIONS_CONTAINER = (By.CSS_SELECTOR, "[data-testid='benchmark-associations']")
    ASSOCIATIONS_TITLE = (By.CSS_SELECTOR, "[data-testid='benchmark-associations'] h3")
    BMKS_ASSOCIATIONS = (
        By.CSS_SELECTOR,
        "[data-testid='benchmark-associations'] [data-testid='associated-benchmark-item']",
    )
    ASSOCIATION_CARDS = (
        By.CSS_SELECTOR,
        "[data-testid='benchmark-associations'] [data-testid='associated-benchmark-item'] a",
    )

    BMK_DATA = (By.CSS_SELECTOR, "div.font-semibold")
    BMK_VIEW = (By.XPATH, ".//a[contains(@href,'/benchmarks/ui/display/')]")
    BMK_ASSOCIATE = (By.CSS_SELECTOR, "[data-testid='request-bmk-association']")

    APPROVED_BMKS = (
        By.XPATH,
        "//div[contains(@class,'medperf-bg')][.//form[starts-with(@id,'run-all-')]]"
        "/parent::div",
    )

    BMK_LABEL = (By.XPATH, ".//div[contains(@class,'medperf-bg')]//h4")
    BMK_NAME = (By.XPATH, ".//div[contains(@class,'medperf-bg')]//h4//a")
    BMK_RUN_ALL = (By.CSS_SELECTOR, "button.run-all-btn")

    REF_MODEL_LABEL = (
        By.XPATH,
        ".//small[contains(normalize-space(.), 'Reference Model')]",
    )
    REF_MODEL = (
        By.XPATH,
        ".//small[contains(normalize-space(.), 'Reference Model')]"
        "/following::a[contains(@href,'/models/')][1]",
    )
    REF_MODEL_DATE = (
        By.XPATH,
        ".//small[contains(normalize-space(.), 'Reference Model')]"
        "/following::small[@data-date][1]",
    )
    REF_MODEL_STATE = (
        By.XPATH,
        ".//small[contains(normalize-space(.), 'Reference Model')]"
        "/following::i[contains(@class,'fa-check-circle')][1]",
    )
    REF_MODEL_CARD = (
        By.XPATH,
        ".//small[contains(normalize-space(.), 'Reference Model')]"
        "/ancestor::div[contains(@class,'flex-wrap')]"
        "[contains(@class,'justify-between')][1]",
    )

    MODEL = (
        By.XPATH,
        ".//div[contains(@class,'model-info')]//a[contains(@href,'/models/')]",
    )
    MODEL_DATE = (
        By.XPATH,
        ".//div[contains(@class,'model-info')]//small[@data-date]",
    )
    MODEL_STATE = (
        By.XPATH,
        ".//div[contains(@class,'model-info')]//i[contains(@class,'fa-check-circle')]",
    )
    MODEL_CARD = (
        By.XPATH,
        ".//div[contains(@class,'model-info')]"
        "/ancestor::div[contains(@class,'flex-wrap')]"
        "[contains(@class,'justify-between')][1]",
    )

    RUN_MODEL_BTN = (
        By.XPATH,
        ".//form[contains(@action,'/datasets/run')]//button[contains(@type,'submit')]",
    )
    VIEW_RESULT_BTN = (By.CSS_SELECTOR, "button.view-result-btn")
    SUBMIT_BTN = (
        By.XPATH,
        ".//form[contains(@action,'/datasets/submit_result')]//button[@type='submit']",
    )
    ALL_SUBMIT_RESULT_BTNS = (
        By.XPATH,
        "//form[contains(@action,'/datasets/submit_result')]//button[@type='submit']",
    )

    RESUME_SCRIPT_PREPARE = (
        By.XPATH,
        "//script[contains(text(), 'resumeRunningTask(\"#prepare-dataset-form\")')]",
    )
    RESUME_SCRIPT_SET_OPERATIONAL = (
        By.XPATH,
        "//script[contains(text(), 'resumeRunningTask(\"#set-operational-form\")')]",
    )
    RESUME_SCRIPT_ASSOCIATE = (
        By.XPATH,
        "//script[contains(text(), 'resumeRunningTask(\"#dataset-association-form-')]",
    )
    RESUME_SCRIPT_RUN_EXECUTION = (
        By.XPATH,
        "//script[contains(text(), 'resumeRunningTask(\"#run-')]",
    )
    RESUME_SCRIPT_SUBMIT_RESULT = (
        By.XPATH,
        "//script[contains(text(), 'resumeRunningTask(\"#submit-')]",
    )
    SUBMITTED_TEXT = (
        By.XPATH,
        ".//span[contains(@class,'rounded-lg')][contains(.,'Submitted')]",
    )

    CLOSE_BTN = (By.CSS_SELECTOR, "#page-modal-footer button.close-modal-btn")

    STOP_BTN = (By.ID, "stop-training-btn")

    def __init__(self, driver, dataset="", benchmark=""):
        super().__init__(driver)
        self.DATASET_NAME_BTN = (
            By.XPATH,
            f'//h3//a[@data-testid="dset-name" and contains(text(), "{dataset}")]',
        )
        self.RUN_BTN = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            f'//button[contains(@class,"run-all-btn")]',
        )
        self.VIEW_BTNS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            f'//button[contains(@class,"view-result-btn")]',
        )
        self.SUBMIT_BTNS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            f'//form[contains(@action,"submit_result")]//button',
        )

        self.ASSOCIATE_BTN = (
            By.XPATH,
            f'//div[.//div[contains(normalize-space(.), "{benchmark}")]]'
            f'//button[@data-testid="request-bmk-association"]',
        )

    def _action_card_titles(self):
        return self.driver.find_elements(*self.ACTION_GRID_CARDS)

    def disabled_set_operational_title(self):
        cards = self._action_card_titles()
        return cards[1].find_element(
            By.XPATH,
            ".//span[contains(@class,'font-semibold')][contains(.,'operational')]",
        )

    def disabled_associate_title(self):
        cards = self._action_card_titles()
        return cards[2].find_element(
            By.XPATH,
            ".//span[contains(@class,'font-semibold')][contains(.,'Associate')]",
        )

    def prepare_dataset(self):
        self.click(self.PREPARE_BTN)

    def set_operational(self):
        self.click(self.SET_OPERATIONAL_BTN)

    def request_association(self):
        self.click(self.DROPDOWN_BTN)
        self.click(self.ASSOCIATE_BTN)

    def get_association_cards_titles(self):
        return [i.text for i in self.driver.find_elements(*self.ASSOCIATION_CARDS)]

    def run_execution(self):
        self.click(self.RUN_BTN)

    def __view_result(self, view_btn):
        self.ensure_element_ready(view_btn)
        view_btn.click()
        view_modal = self.find(self.PAGE_MODAL)
        self.wait_for_visibility_element(view_modal)
        view_modal.find_element(*self.CLOSE_BTN).click()
        self.wait_for_invisibility_element(view_modal)

    def view_results(self):
        view_btns = self.driver.find_elements(*self.VIEW_BTNS)
        for view_btn in view_btns:
            self.__view_result(view_btn)

    def submit_result(self, submit_btn):
        self.ensure_element_ready(submit_btn)
        submit_btn.click()

    def get_submit_buttons(self):
        return self.driver.find_elements(*self.SUBMIT_BTNS)

    TRAINING_ASSOCIATE_DROPDOWN_BTN = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Associate with training experiment')]",
    )

    def request_training_association_for_experiment(self, experiment_name: str):
        self.click(self.TRAINING_ASSOCIATE_DROPDOWN_BTN)
        req_btn_locator = (
            By.XPATH,
            "//div[@id='dropdown-training-div']"
            "//div[contains(@class,'font-semibold')]"
            f"[contains(., '{experiment_name}')]"
            "/ancestor::div[contains(@class,'py-3')][1]"
            "//form[@action='/datasets/associate_training']"
            "//button[@type='submit']",
        )
        el = self.find(req_btn_locator)
        self.ensure_element_ready(el)
        el.click()

    def start_training_for_experiment(self, experiment_name: str):
        form_submit = (
            By.XPATH,
            "//li[.//a[contains(., '"
            + experiment_name
            + "')]]//form[starts-with(@id,'start-training-form-')]"
            "//button[@type='submit']",
        )
        el = self.find(form_submit)
        self.ensure_element_ready(el)
        el.click()

    def stop_training(self):
        self.click(self.STOP_BTN)
