from selenium.webdriver.common.by import By

from ..base_page import BasePage


class ContainerDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='container-header']")
    DETAILS_HEADING = (By.CSS_SELECTOR, "[data-testid='container-details-heading']")
    STATE_BADGES = (By.CSS_SELECTOR, "[data-testid='container-state'], [data-testid='container-validity']")

    CONTAINER_ID_LABEL = (By.CSS_SELECTOR, "[data-testid='container-id-label']")
    CONTAINER_ID_VALUE = (By.CSS_SELECTOR, "[data-testid='container-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='container-owner-label']")
    OWNER_VALUE = (By.CSS_SELECTOR, "[data-testid='container-owner']")

    MANIFEST_LABEL = (By.CSS_SELECTOR, "[data-testid='container-manifest-label']")
    MANIFEST_YAML_BTN = (By.CSS_SELECTOR, "[data-testid='container-manifest-yaml-btn']")
    PARAMETERS_LABEL = (By.CSS_SELECTOR, "[data-testid='container-parameters-label']")
    PARAMETERS_YAML_BTN = (By.CSS_SELECTOR, "[data-testid='container-parameters-yaml-btn']")
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

    RESUME_SCRIPT = (
        By.XPATH,
        "//script[not(@src)][contains(., 'resumeRunningTask')]",
    )

    # Model / legacy association UI (e2e & older flows; not on minimal container detail)
    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    ASSOCIATION_CARDS = (
        By.CSS_SELECTOR,
        "div[data-testid='benchmark-associations'] div[data-testid='associated-benchmark-item'] a",
    )
    BENCHMARK = (By.ID, "benchmark")
    EMAILS = (By.ID, "email-input")
    GRANT_ACCESS = (By.ID, "grant-access-btn")
    DELETE_KEYS = (By.ID, "delete-keys-btn")

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
        return [i.text for i in self.driver.find_elements(*self.ASSOCIATION_CARDS)]

    def grant_access(self, benchmark, emails):
        self.select_by_text(self.BENCHMARK, benchmark)
        self.type(self.EMAILS, ",".join(emails) + ",")
        self.click(self.GRANT_ACCESS)

    def delete_keys(self):
        self.click(self.DELETE_KEYS)
