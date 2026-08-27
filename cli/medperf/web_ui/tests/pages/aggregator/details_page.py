from selenium.webdriver.common.by import By

from ..base_page import BasePage


class AggregatorDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='aggregator-header']")
    DETAILS_HEADING = (By.CSS_SELECTOR, "[data-testid='aggregator-details-heading']")
    EXPERIMENTS_HEADING = (
        By.CSS_SELECTOR,
        "[data-testid='aggregator-experiments-heading']",
    )
    ACTIONS_HEADING = (By.CSS_SELECTOR, "[data-testid='aggregator-actions-heading']")

    ID_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-id-label']")
    ID = (By.CSS_SELECTOR, "[data-testid='aggregator-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-owner-label']")
    OWNER = (By.CSS_SELECTOR, "[data-testid='aggregator-owner']")
    ADDRESS_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-address-label']")
    ADDRESS = (By.CSS_SELECTOR, "[data-testid='aggregator-address']")
    PORT_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-port-label']")
    PORT = (By.CSS_SELECTOR, "[data-testid='aggregator-port']")
    ADMIN_PORT_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-admin-port-label']")
    ADMIN_PORT = (By.CSS_SELECTOR, "[data-testid='aggregator-admin-port']")
    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='aggregator-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='aggregator-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='aggregator-modified']")

    GET_CERT_FORM = (By.ID, "get-server-cert-form")
    START_FORM = (By.ID, "start-aggregator-form")
    RUN_BTN = (By.ID, "run-aggregator-btn")
    STOP_BTN = (By.ID, "stop-aggregator-btn")

    RESUME_SCRIPT_GET_CERT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#get-server-cert-form\")')]",
    )
    RESUME_SCRIPT_RUN = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#start-aggregator-form\")')]",
    )

    GET_CERT_SUBMIT = (
        By.CSS_SELECTOR,
        "#get-server-cert-form button[type='submit']",
    )
    # The training-experiment picker is a searchable_select widget (hidden
    # input + JS-driven query/listbox), not a real <select> element.
    TRAINING_EXP_SELECT = (By.ID, "training-exp-id")
    PUBLISH_ON_INPUT = (By.ID, "publish-on-input")

    def get_server_certificate(self):
        self.click(self.GET_CERT_SUBMIT)

    def run_aggregator_for_experiment(self, experiment_name: str, publish_on: str = ""):
        self.select_searchable_entity(self.TRAINING_EXP_SELECT, experiment_name)
        if publish_on:
            el = self.find(self.PUBLISH_ON_INPUT)
            self.ensure_element_ready(el)
            el.clear()
            el.send_keys(publish_on)
        self.click(self.RUN_BTN)
