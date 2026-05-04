from selenium.webdriver.common.by import By
from ..base_page import BasePage


class DatasetsPage(BasePage):
    REG_DSET_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-dset-btn"]')
    IMPORT_DSET_BTN = (By.CSS_SELECTOR, 'a[data-testid="import-dset-btn"]')
    HEADER = (By.CSS_SELECTOR, 'h1[data-testid="page-header"]')
    TITLE = HEADER

    MINE_LABEL = (
        By.XPATH,
        "//label[.//input[@id='switch']]//span[contains(@class,'font-semibold')]",
    )
    MINE_INPUT = (By.ID, "switch")

    CARDS_CONTAINER = (
        By.CSS_SELECTOR,
        'div[data-testid="cards-container"] div.medperf-card',
    )
    CARD_TITLE = (By.CSS_SELECTOR, 'a[data-testid="dset-name"]')
    CARD_ID = (By.CSS_SELECTOR, '[data-testid="dset-id"]')
    CARD_STATE = (By.CSS_SELECTOR, '[data-testid="dset-state"]')
    CARD_VALID = (By.CSS_SELECTOR, '[data-testid="dset-is-valid"]')
    CARD_DESC = (By.CSS_SELECTOR, "[data-testid='dset-description']")
    CARD_CREATED = (By.CSS_SELECTOR, '[data-testid="dset-created-at"]')
    CARD_LOCATION = (By.CSS_SELECTOR, "[data-testid='dset-location']")
    NO_DATASETS = (By.CSS_SELECTOR, '[data-testid="no-dsets-msg"]')

    def toggle_mine(self):
        el = self.find(self.MINE_INPUT)
        self.driver.execute_script("arguments[0].click();", el)

    def is_mine(self):
        return "?mine_only=true" in self.current_url

    def not_mine(self):
        return "?mine_only=true" not in self.current_url
