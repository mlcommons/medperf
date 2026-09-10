from selenium.webdriver.common.by import By
from ..base_page import BasePage


class DatasetDetailsPage(BasePage):

    PREPARE_BTN = (By.ID, "prepare-dataset")
    PREPARED_TEXT = (By.CSS_SELECTOR, 'div[data-testid="prepared-section"]')

    SET_OPERATIONAL_BTN = (By.ID, "set-operational")
    SET_OPERATIONAL_TEXT = (By.CSS_SELECTOR, 'div[data-testid="operational-section"]')

    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    ASSOCIATION_CARDS = (
        By.CSS_SELECTOR,
        "div[data-testid='benchmark-associations'] div[data-testid='associated-benchmark-item'] a",
    )

    CLOSE_BTN = (By.CSS_SELECTOR, "#page-modal-footer button.close-modal-btn")

    def __init__(self, driver, dataset, benchmark=""):
        super().__init__(driver)
        self.DATASET_NAME_BTN = (
            By.XPATH,
            f'//h3//a[@data-testid="dset-name" and contains(text(), "{dataset}")]',
        )
        self.RUN_BTN = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]//button[contains(@class,"run-all-btn")]',
        )
        self.VIEW_BTNS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]//button[contains(@class,"view-result-btn")]',
        )
        self.SUBMIT_BTNS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            + '//form[contains(@action,"submit_result")]//button',
        )
        self.COLLECT_FORMS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            + '//form[contains(@action,"download_cc_results")]',
        )

        self.ASSOCIATE_BTN = (
            By.XPATH,
            f'//div[.//div[contains(normalize-space(.), "{benchmark}")]]//button[@data-testid="request-bmk-association"]',
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

    def collect_results(self, collect_form, execution_id):
        """Asks for the results of a confidential execution somebody else ran.

        The id is typed rather than picked from the page: an execution is
        recorded as its operator's, so a collector who did not operate it has
        nothing to list. The operator is told the number when their run ends
        and hands it over -- the same number the CLI's `-e` takes.
        """
        field = collect_form.find_element(By.NAME, "execution_id")
        self.ensure_element_ready(field)
        field.clear()
        field.send_keys(str(execution_id))

        submit_btn = collect_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        self.ensure_element_ready(submit_btn)
        submit_btn.click()

    def get_collect_forms(self):
        return self.driver.find_elements(*self.COLLECT_FORMS)
