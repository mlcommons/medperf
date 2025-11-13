from selenium.webdriver.common.by import By
from ..base_page import BasePage


class DatasetsPage(BasePage):
    REG_DSET_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-dset-btn"]')
    IMPORT_DSET_BTN = (By.CSS_SELECTOR, 'a[data-testid="import-dset-btn"]')
    TITLE = (By.CSS_SELECTOR, 'h1[data-testid="page-header"]')
    MINE_LABEL = (By.ID, "switch")
    MINE_SWITCH = (By.CSS_SELECTOR, 'label[for="switch"]')
    CARDS_CONTAINER = (By.CSS_SELECTOR, 'div[data-testid="cards-container"] div.card')
    CARD_TITLE = (By.CSS_SELECTOR, 'h5 > a[data-testid="dset-name"]')
    CARD_ID = (By.CSS_SELECTOR, 'h6[data-testid="dset-id"]')
    CARD_STATE = (By.CSS_SELECTOR, 'h6[data-testid="dset-state"]')
    CARD_VALID = (By.CSS_SELECTOR, 'h6[data-testid="dset-is-valid"]')
    CARD_DESC_TITLE = (By.CSS_SELECTOR, 'p[data-testid="dset-description"] > strong')
    CARD_DESC = (By.CSS_SELECTOR, 'p[data-testid="dset-description"]')
    CARD_CREATED = (By.CSS_SELECTOR, 'p[data-testid="dset-created-at"] > small')
    CARD_LOCATION = (By.CSS_SELECTOR, 'p[data-testid="dset-location"] > small')
    NO_DATASETS = (By.CSS_SELECTOR, '[data-testid="no-dsets-msg"]')

    def toggle_mine(self):
        self.click(self.MINE_SWITCH)

    def is_mine(self):
        return "?mine_only=true" in self.current_url

    def not_mine(self):
        return "?mine_only=true" in self.current_url
