from selenium.webdriver.common.by import By
from ..base_page import BasePage


class ContainerDetailsPage(BasePage):
    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='benchmark-associations-btn']",
    )
    ASSOCIATIONS_LIST = (By.ID, "benchmark-associations-list")
    ASSOCIATION_CARDS = (
        By.CSS_SELECTOR,
        "div[data-testid='benchmark-associations'] div[data-testid='associated-benchmark-item'] a",
    )
    MANAGE_ACCESS = (By.CSS_SELECTOR, "a[data-testid='manage-access']")

    BENCHMARK = (By.ID, "benchmark")
    EMAILS = (By.ID, "email-input")
    GRANT_ACCESS = (By.ID, "grant-access-btn")
    DELETE_KEYS = (By.ID, "delete-keys-btn")

    def __init__(self, driver, container, benchmark):
        super().__init__(driver)
        self.CONTAINER_BTN = (
            By.XPATH,
            f'//h3//a[@data-testid="cont-name" and contains(text(), "{container}")]',
        )
        self.ASSOCIATE_BTN = (
            By.XPATH,
            f'//div[div[contains(text(), "{benchmark}")]]//button[@data-testid="request-bmk-association"]',
        )
        self.RUN_BTN = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            + '//button[contains(@class,"run-all-btn")]',
        )
        self.COLLECT_FORMS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            + '//form[contains(@action,"download_cc_results")]',
        )
        self.COLLECTOR_EXECUTIONS = (
            By.XPATH,
            f'//div[.//h4//a/strong[contains(normalize-space(.), "{benchmark}")]]'
            + '//span[@data-testid="collector-execution"]',
        )

    def request_association(self):
        self.click(self.DROPDOWN_BTN)
        self.click(self.ASSOCIATE_BTN)

    def run_execution(self):
        self.click(self.RUN_BTN)

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

    def get_collector_execution_ids(self):
        """The executions this operator ran whose results went to somebody else.

        What the operator has to hand over: the collector cannot list them.
        """
        return [
            element.get_attribute("data-execution-id")
            for element in self.driver.find_elements(*self.COLLECTOR_EXECUTIONS)
        ]

    def get_association_cards_titles(self):
        self.click(self.ASSOCIATIONS_BTN)
        associations = self.find(self.ASSOCIATIONS_LIST)
        self.wait_for_visibility_element(associations)
        return [i.text for i in self.driver.find_elements(*self.ASSOCIATION_CARDS)]

    def grant_access(self, benchmark, emails):
        self.select_searchable_entity(self.BENCHMARK, benchmark)
        self.type(self.EMAILS, ",".join(emails) + ",")
        self.click(self.GRANT_ACCESS)

    def delete_keys(self):
        self.click(self.DELETE_KEYS)
