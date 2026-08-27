from selenium.webdriver.common.by import By

from ..base_page import BasePage


class ContainerDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='container-header']")
    DETAILS_HEADING = (By.CSS_SELECTOR, "[data-testid='container-details-heading']")
    STATE_BADGES = (
        By.CSS_SELECTOR,
        "[data-testid='container-state'], [data-testid='container-validity']",
    )

    CONTAINER_ID_LABEL = (By.CSS_SELECTOR, "[data-testid='container-id-label']")
    CONTAINER_ID_VALUE = (By.CSS_SELECTOR, "[data-testid='container-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='container-owner-label']")
    OWNER_VALUE = (By.CSS_SELECTOR, "[data-testid='container-owner']")

    MANIFEST_LABEL = (By.CSS_SELECTOR, "[data-testid='container-manifest-label']")
    MANIFEST_YAML_BTN = (By.CSS_SELECTOR, "[data-testid='container-manifest-yaml-btn']")
    PARAMETERS_LABEL = (By.CSS_SELECTOR, "[data-testid='container-parameters-label']")
    PARAMETERS_YAML_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='container-parameters-yaml-btn']",
    )
    PARAMETERS_NA = (By.CSS_SELECTOR, "[data-testid='container-parameters-na']")
    ADDITIONAL_LABEL = (By.CSS_SELECTOR, "[data-testid='container-additional-label']")
    ADDITIONAL_LINK = (By.CSS_SELECTOR, "[data-testid='container-additional-link']")
    ADDITIONAL_NA = (By.CSS_SELECTOR, "[data-testid='container-additional-na']")

    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='container-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='container-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='container-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='container-modified']")

    MANAGE_ACCESS = (By.CSS_SELECTOR, "a[data-testid='manage-access']")

    ACCESS_SECTION = (By.CSS_SELECTOR, "[data-testid='container-access-label']")

    ACCESS_HEADER = (By.CSS_SELECTOR, "h1")

    GRANT_FORM = (By.ID, "grant-access-form")
    BENCHMARK = (By.ID, "benchmark")
    EMAIL_INPUT = (By.ID, "email-input")
    GRANT_BTN = (By.ID, "grant-access-btn")

    BENCHMARK_AUTO = (By.ID, "benchmark-auto")
    INTERVAL_AUTO = (By.ID, "interval-auto")
    EMAIL_INPUT_AUTO = (By.ID, "email-input-auto")
    START_AUTO_BTN = (By.ID, "start-auto-access-btn")
    STOP_AUTO_BTN = (By.ID, "stop-auto-access-btn")
    RUNNING_BADGE = (By.ID, "running-badge")

    NO_KEYS_MSG = (By.XPATH, "//p[contains(., 'No users currently have access')]")
    KEYS_TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")

    DELETE_KEYS_FORM = (By.ID, "delete-keys-form")
    DELETE_KEYS_BTN = (By.ID, "delete-keys-btn")

    RESUME_SCRIPT = (
        By.XPATH,
        "//script[not(@src)][contains(., 'resumeRunningTask')]",
    )

    # Model / legacy association UI (e2e & older flows; not on minimal container detail)
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

    def __init__(self, driver, container="", benchmark=""):
        super().__init__(driver)
        self.CONTAINER_BTN = (
            By.XPATH,
            f'//h3//a[@data-testid="cont-name" and contains(text(), "{container}")]',
        )
        self.ASSOCIATE_BTN = (
            By.XPATH,
            f'//div[div[contains(text(), "{benchmark}")]]//button[@data-testid="request-bmk-association"]',
        )

    def request_association(self):
        self.click(self.DROPDOWN_BTN)
        self.click(self.ASSOCIATE_BTN)

    def get_association_cards_titles(self):
        self.click(self.ASSOCIATIONS_BTN)
        associations = self.find(self.ASSOCIATIONS_LIST)
        self.wait_for_visibility_element(associations)
        return [i.text for i in self.driver.find_elements(*self.ASSOCIATION_CARDS)]

    def revoke_btn(self, key_id):
        return (By.ID, f"revoke-btn-{key_id}")

    def grant_access(self, benchmark, emails):
        self.select_searchable_entity(self.BENCHMARK, benchmark)
        self.type(self.EMAIL_INPUT, ",".join(emails) + ",")
        self.click(self.GRANT_BTN)

    def revoke_access(self, key_id):
        self.click(self.revoke_btn(key_id))

    def delete_keys(self):
        self.click(self.DELETE_KEYS_BTN)

    def start_auto_access(self, benchmark, emails):
        self.select_searchable_entity(self.BENCHMARK_AUTO, benchmark)
        self.type(self.EMAIL_INPUT_AUTO, ",".join(emails) + ",")
        self.click(self.START_AUTO_BTN)

    def stop_auto_access(self):
        self.click(self.STOP_AUTO_BTN)
