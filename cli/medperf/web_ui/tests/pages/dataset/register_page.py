from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegDatasetPage(BasePage):
    REG_DSET_BTN = (By.CSS_SELECTOR, '[data-testid="reg-dset-btn"]')
    BENCHMARK = (By.ID, "benchmark")
    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    LOCATION = (By.ID, "location")
    DATA = (By.ID, "data-path")
    LABELS = (By.ID, "labels-path")
    REGISTER = (By.ID, "register-dataset-btn")

    def register_dataset(
        self,
        benchmark,
        name,
        description,
        location,
        data_path,
        labels_path,
    ):
        self.select_by_text(self.BENCHMARK, benchmark)

        self.type(self.NAME, name)
        self.type(self.DESCRIPTION, description)
        self.type(self.LOCATION, location)
        self.type(self.DATA, data_path)
        self.type(self.LABELS, labels_path)

        self.click(self.REGISTER)
