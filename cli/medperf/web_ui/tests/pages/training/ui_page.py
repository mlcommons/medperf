from selenium.webdriver.common.by import By

from ..base_page import BasePage


class TrainingPage(BasePage):
    REG_TRAINING_BTN = (By.CSS_SELECTOR, 'a[data-testid="reg-training-btn"]')
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
    CARD_TITLE = (By.CSS_SELECTOR, 'a[data-testid="training-name"]')
    CARD_ID = (By.CSS_SELECTOR, '[data-testid="training-id"]')
    CARD_STATE = (By.CSS_SELECTOR, '[data-testid="training-state"]')
    CARD_APPROVAL = (By.CSS_SELECTOR, '[data-testid="training-approval"]')
    CARD_CREATED = (By.CSS_SELECTOR, '[data-testid="training-created-at"]')
    NO_EXPERIMENTS = (By.CSS_SELECTOR, '[data-testid="no-exps-msg"]')

    def toggle_mine(self):
        el = self.find(self.MINE_INPUT)
        self.driver.execute_script("arguments[0].click();", el)

    def is_mine(self):
        return "?mine_only=true" in self.current_url

    def not_mine(self):
        return "?mine_only=true" not in self.current_url

    def open_experiment_by_name(self, name: str):
        link = self.find(
            (
                By.XPATH,
                f'//a[@data-testid="training-name" and contains(normalize-space(.), "{name}")]',
            )
        )
        self.ensure_element_ready(link)
        old_url = self.current_url
        link.click()
        self.wait_for_url_change(old_url)
        self.wait_for_presence_selector(self.NAVBAR)

    def get_training_exp_id(self):
        id_text = self.get_text(self.CARD_ID)
        return int(id_text)
