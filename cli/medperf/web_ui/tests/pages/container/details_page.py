from selenium.webdriver.common.by import By
from ..base_page import BasePage


class ContainerDetailsPage(BasePage):
    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    ASSOCIATION_CARDS = (By.CSS_SELECTOR, "div.card.association-card .card-title > a")

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
