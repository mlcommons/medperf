from selenium.webdriver.common.by import By
from ..base_page import BasePage


class BenchmarksPage(BasePage):
    REG_BMK_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-bmk-btn"]')
    HEADER = (By.CSS_SELECTOR, 'h1[data-testid="page-header"]')
    TITLE = HEADER

    MINE_LABEL = (
        By.XPATH,
        "//label[.//input[@id='switch']]//span[contains(@class,'font-medium')]",
    )
    MINE_INPUT = (By.ID, "switch")

    SEARCH_INPUT = (By.ID, "listing-search")
    SEARCH_BTN = (By.ID, "listing-search-btn")
    ORDERING_SELECT = (By.ID, "ordering")
    PAGE_SIZE_SELECT = (By.ID, "page-size")

    CARDS_CONTAINER = (
        By.CSS_SELECTOR,
        'div[data-testid="cards-container"] div.medperf-card',
    )
    CARD_TITLE = (By.CSS_SELECTOR, 'a[data-testid="bmk-name"]')
    CARD_ID = (By.CSS_SELECTOR, '[data-testid="bmk-id"]')
    CARD_STATE = (By.CSS_SELECTOR, '[data-testid="bmk-state"]')
    CARD_VALID = (By.CSS_SELECTOR, '[data-testid="bmk-is-valid"]')
    CARD_DESC = (By.CSS_SELECTOR, "[data-testid='bmk-description']")
    CARD_DOCS = (By.CSS_SELECTOR, "[data-testid='bmk-docs']")
    CARD_CREATED = (By.CSS_SELECTOR, '[data-testid="bmk-created-at"]')
    NO_BENCHMARKS = (By.CSS_SELECTOR, '[data-testid="no-bmks-msg"]')
    APPROVAL = (By.CSS_SELECTOR, "[data-testid='bmk-approval-status']")

    def toggle_mine(self):
        el = self.find(self.MINE_INPUT)
        self.driver.execute_script("arguments[0].click();", el)

    def is_mine(self):
        return "mine_only=true" in self.current_url

    def not_mine(self):
        return "mine_only=true" not in self.current_url

    def search(self, query):
        self.type(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_BTN)

    def set_ordering(self, option_text):
        self.select_by_text(self.ORDERING_SELECT, option_text)

    def set_page_size(self, size):
        self.select_by_text(self.PAGE_SIZE_SELECT, str(size))

    def page_link(self, n):
        return (By.CSS_SELECTOR, f'a.page-link[data-page="{n}"]')
