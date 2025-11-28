from selenium.webdriver.common.by import By
from ..base_page import BasePage


class ContainerDetailsPage(BasePage):
    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    ASSOCIATION_CARDS = (By.CSS_SELECTOR, "div.card.association-card .card-title > a")
    MANAGE_ACCESS = (By.CSS_SELECTOR, "a[data-test-id='manage-access']")

    BENCHMARK = (By.ID, "benchmark")
    EMAILS = (By.ID, "email-input")
    GRANT_ACCESS = (By.ID, "grant-access-btn")
    DELETE_KEYS = (By.ID, "delete-keys-btn")

    def __init__(self, driver, container, benchmark):
        super().__init__(driver)
        self.CONTAINER_BTN = (
            By.XPATH,
            f'//h5//a[@data-testid="cont-name" and contains(text(), "{container}")]',
        )
        self.ASSOCIATE_BTN = (
            By.XPATH,
            f'//li[.//strong[contains(text(), "{benchmark}")]]//button[contains(@class, "request-association-btn")]',
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
