from selenium.webdriver.common.by import By
from ..base_page import BasePage


class ContainersPage(BasePage):
    REG_DSET_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-cont-btn"]')
    TITLE = (By.CSS_SELECTOR, 'h1[data-testid="page-header"]')
    MINE_LABEL = (By.ID, "switch")
    MINE_SWITCH = (By.CSS_SELECTOR, 'label[for="switch"]')
    CARDS_CONTAINER = (By.CSS_SELECTOR, 'div[data-testid="cards-container"] div.card')
    CARD_TITLE = (By.CSS_SELECTOR, 'h5 > a[data-testid="cont-name"]')
    CARD_ID = (By.CSS_SELECTOR, 'h6[data-testid="cont-id"]')
    CARD_STATE = (By.CSS_SELECTOR, 'h6[data-testid="cont-state"]')
    CARD_VALID = (By.CSS_SELECTOR, 'h6[data-testid="cont-is-valid"]')
    CARD_CREATED = (By.CSS_SELECTOR, 'p[data-testid="cont-created-at"] > small')
    NO_CONTAINERS = (By.CSS_SELECTOR, '[data-testid="no-conts-msg"]')

    def toggle_mine(self):
        self.click(self.MINE_SWITCH)

    def is_mine(self):
        return "?mine_only=true" in self.current_url

    def not_mine(self):
        return "?mine_only=true" in self.current_url
