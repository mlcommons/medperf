from selenium.webdriver.common.by import By
from ..base_page import BasePage


class BenchmarksPage(BasePage):
    REG_BMK_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-bmk-btn"]')
    TITLE = (By.CSS_SELECTOR, 'h1[data-testid="page-header"]')
    MINE_LABEL = (By.ID, "switch")
    MINE_SWITCH = (By.CSS_SELECTOR, 'label[for="switch"]')
    CARDS_CONTAINER = (By.CSS_SELECTOR, 'div[data-testid="cards-container"] div.card')
    CARD_TITLE = (By.CSS_SELECTOR, 'h5 > a[data-testid="bmk-name"]')
    CARD_ID = (By.CSS_SELECTOR, 'h6[data-testid="bmk-id"]')
    CARD_STATE = (By.CSS_SELECTOR, 'h6[data-testid="bmk-state"]')
    CARD_VALID = (By.CSS_SELECTOR, 'h6[data-testid="bmk-is-valid"]')
    CARD_DESC = (By.CSS_SELECTOR, "[data-testid='bmk-description']")
    CARD_DOCS = (By.CSS_SELECTOR, "[data-testid='bmk-docs']")
    CARD_CREATED = (By.CSS_SELECTOR, 'p[data-testid="bmk-created-at"] > small')
    NO_BENCHMARKS = (By.CSS_SELECTOR, '[data-testid="no-bmks-msg"]')
    APPROVAL = (By.CSS_SELECTOR, "[data-testid='bmk-approval-status']")

    def toggle_mine(self):
        self.click(self.MINE_SWITCH)

    def is_mine(self):
        return "?mine_only=true" in self.current_url

    def not_mine(self):
        return "?mine_only=true" in self.current_url
