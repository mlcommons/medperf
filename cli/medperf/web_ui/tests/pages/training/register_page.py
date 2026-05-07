from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegTrainingPage(BasePage):
    FORM = (By.ID, "register-training-form")
    HEADER = (By.CSS_SELECTOR, "[data-testid='training-register-header']")

    NAME_LABEL = (By.CSS_SELECTOR, "[data-testid='training-register-name-label']")
    DESCRIPTION_LABEL = (
        By.CSS_SELECTOR,
        "[data-testid='training-register-description-label']",
    )
    DATA_PREP_LABEL = (
        By.CSS_SELECTOR,
        "[data-testid='training-register-data-prep-label']",
    )
    FL_LABEL = (By.CSS_SELECTOR, "[data-testid='training-register-fl-label']")

    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    DATA_PREP = (By.ID, "data-preparation-container")
    FL = (By.ID, "fl-container")
    FL_ADMIN = (By.ID, "fl-admin-container")
    REGISTER = (By.ID, "register-training-btn")

    NAME_TOOLTIP = (By.CSS_SELECTOR, "[data-testid='training-register-name-tooltip']")
    DESCRIPTION_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='training-register-description-tooltip']",
    )
    DATA_PREP_TOOLTIP = (
        By.CSS_SELECTOR,
        "[data-testid='training-register-data-prep-tooltip']",
    )
    RESUME_SCRIPT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#register-training-form\")')]",
    )

    def register_training(
        self,
        name,
        description,
        data_prep,
        fl_container,
        fl_admin_container="None",
    ):
        self.type(self.NAME, name)
        self.type(self.DESCRIPTION, description)
        self.select_by_text(self.DATA_PREP, data_prep)
        self.select_by_text(self.FL, fl_container)
        self.select_by_text(self.FL_ADMIN, fl_admin_container)
        self.click(self.REGISTER)
