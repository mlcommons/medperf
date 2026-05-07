from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegDatasetPage(BasePage):
    REG_DSET_BTN = (By.CSS_SELECTOR, '[data-testid="reg-dset-btn"]')

    FORM = (By.ID, "register-dataset-form")
    HEADER = (By.CSS_SELECTOR, "h1.text-3xl")

    BENCHMARK = (By.ID, "benchmark")
    DATA_PREP = (By.ID, "data-preparation-container")
    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    LOCATION = (By.ID, "location")
    DATA = (By.ID, "data-path")
    LABELS = (By.ID, "labels-path")
    DATA_BROWSE = (By.ID, "browse-data-btn")
    LABELS_BROWSE = (By.ID, "browse-labels-btn")
    REGISTER = (By.ID, "register-dataset-btn")

    BENCHMARK_LABEL = (By.CSS_SELECTOR, "label[for='benchmark']")
    DATA_PREP_LABEL = (By.CSS_SELECTOR, "label[for='prep_cube_uid']")
    NAME_LABEL = (By.CSS_SELECTOR, "label[for='name']")
    DESCRIPTION_LABEL = (By.CSS_SELECTOR, "label[for='description']")
    LOCATION_LABEL = (By.CSS_SELECTOR, "label[for='location']")
    DATA_LABEL = (By.CSS_SELECTOR, "label[for='data-path']")
    LABELS_LABEL = (By.CSS_SELECTOR, "label[for='labels-path']")

    NAME_TOOLTIP = (
        By.XPATH,
        "//label[@for='name']/following-sibling::div//span[contains(@class,'tooltip-icon')]",
    )
    DESCRIPTION_TOOLTIP = (
        By.XPATH,
        "//label[@for='description']/following-sibling::div//span[contains(@class,'tooltip-icon')]",
    )
    LOCATION_TOOLTIP = (
        By.XPATH,
        "//label[@for='location']/following-sibling::div//span[contains(@class,'tooltip-icon')]",
    )
    DATA_TOOLTIP = (
        By.XPATH,
        "//label[@for='data-path']/following-sibling::div//span[contains(@class,'tooltip-icon')]",
    )
    LABELS_TOOLTIP = (
        By.XPATH,
        "//label[@for='labels-path']/following-sibling::div//span[contains(@class,'tooltip-icon')]",
    )

    PICKER_MODAL = (By.ID, "folder-picker-modal")
    PICKER_PATH = (By.ID, "folder-picker-modal-title")
    PICKER_FOLDERS = (By.CSS_SELECTOR, "#folder-list li")
    PICKER_CANCEL = (By.CSS_SELECTOR, '[data-dismiss-modal="folder-picker-modal"]')
    PICKER_SELECT = (By.ID, "select-folder-btn")

    RESUME_SCRIPT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#register-dataset-form\")')]",
    )

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

    def register_dataset_training(
        self,
        data_prep_name,
        name,
        description,
        location,
        data_path,
        labels_path,
    ):
        self.select_by_text(self.DATA_PREP, data_prep_name)
        self.type(self.NAME, name)
        self.type(self.DESCRIPTION, description)
        self.type(self.LOCATION, location)
        self.type(self.DATA, data_path)
        self.type(self.LABELS, labels_path)
        self.click(self.REGISTER)
