from selenium.webdriver.common.by import By

from ..base_page import BasePage


class TrainingDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='training-header']")
    DETAILS_HEADING = (By.CSS_SELECTOR, "[data-testid='training-details-heading']")
    AGGREGATOR_HEADING = (
        By.CSS_SELECTOR,
        "[data-testid='training-aggregator-heading']",
    )
    ACTIONS_HEADING = (By.CSS_SELECTOR, "[data-testid='training-actions-heading']")
    ASSOCIATIONS_HEADING = (
        By.CSS_SELECTOR,
        "[data-testid='training-associations-heading']",
    )

    STATE = (By.CSS_SELECTOR, "[data-testid='training-state']")
    VALIDITY = (By.CSS_SELECTOR, "[data-testid='training-validity']")
    ID_LABEL = (By.CSS_SELECTOR, "[data-testid='training-id-label']")
    ID = (By.CSS_SELECTOR, "[data-testid='training-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='training-owner-label']")
    OWNER = (By.CSS_SELECTOR, "[data-testid='training-owner']")
    DESCRIPTION_LABEL = (By.CSS_SELECTOR, "[data-testid='training-description-label']")
    DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='training-description']")
    DOCUMENTATION_LABEL = (
        By.CSS_SELECTOR,
        "[data-testid='training-documentation-label']",
    )
    DOCUMENTATION = (
        By.CSS_SELECTOR,
        "[data-testid='training-documentation-link']",
    )
    DOCUMENTATION_NA = (
        By.CSS_SELECTOR,
        "[data-testid='training-documentation-na']",
    )
    DATA_PREP_LABEL = (By.CSS_SELECTOR, "[data-testid='training-data-prep-label']")
    DATA_PREP = (
        By.CSS_SELECTOR,
        "[data-testid='training-data-prep-section'] [data-testid='container-link']",
    )
    FL_LABEL = (By.CSS_SELECTOR, "[data-testid='training-fl-label']")
    FL = (
        By.CSS_SELECTOR,
        "[data-testid='training-fl-section'] [data-testid='container-link']",
    )
    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='training-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='training-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='training-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='training-modified']")

    SET_AGGREGATOR_FORM = (By.ID, "set-aggregator-form")
    SET_PLAN_FORM = (By.ID, "set-plan-form")
    UPDATE_PLAN_FORM = (By.ID, "update-plan-form")
    START_EVENT_FORM = (By.ID, "start-event-form")
    GET_STATUS_FORM = (By.ID, "get-status-form")
    CLOSE_EVENT_FORM = (By.ID, "close-event-form")

    RESUME_SCRIPT_SET_AGGREGATOR = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#set-aggregator-form\")')]",
    )
    RESUME_SCRIPT_SET_PLAN = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#set-plan-form\")')]",
    )
    RESUME_SCRIPT_UPDATE_PLAN = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#update-plan-form\")')]",
    )
    RESUME_SCRIPT_START_EVENT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#start-event-form\")')]",
    )
    RESUME_SCRIPT_CLOSE_EVENT = (
        By.XPATH,
        "//script[contains(., 'resumeRunningTask(\"#close-event-form\")')]",
    )

    # The aggregator picker is a searchable_select widget (hidden input +
    # JS-driven query/listbox), not a real <select> element.
    AGGREGATOR_SELECT = (By.ID, "aggregator-id")
    SET_AGGREGATOR_SUBMIT = (
        By.CSS_SELECTOR,
        "#set-aggregator-form button[type='submit']",
    )
    SET_PLAN_PATH_INPUT = (By.ID, "set-plan-path")
    SET_PLAN_SUBMIT = (By.CSS_SELECTOR, "#set-plan-form button[type='submit']")
    UPDATE_PLAN_FIELD_NAME_INPUT = (
        By.CSS_SELECTOR,
        "#update-plan-form input[name='field_name']",
    )
    UPDATE_PLAN_FIELD_VALUE_INPUT = (
        By.CSS_SELECTOR,
        "#update-plan-form input[name='field_value']",
    )
    UPDATE_PLAN_SUBMIT = (By.CSS_SELECTOR, "#update-plan-form button[type='submit']")
    START_EVENT_NAME_INPUT = (
        By.CSS_SELECTOR,
        "#start-event-form input[name='event_name']",
    )
    START_EVENT_PARTICIPANTS_INPUT = (By.ID, "start-event-participants-path")
    START_EVENT_SUBMIT = (By.CSS_SELECTOR, "#start-event-form button[type='submit']")
    CLOSE_EVENT_SUBMIT = (By.CSS_SELECTOR, "#close-event-form button[type='submit']")
    GET_STATUS_SUBMIT = (By.CSS_SELECTOR, "#get-status-form button[type='submit']")
    APPROVE_DATASET_BUTTONS = (
        By.CSS_SELECTOR,
        "form[action='/training/approve'] button[type='submit']",
    )
    REJECT_DATASET_BUTTONS = (
        By.CSS_SELECTOR,
        "form[action='/training/reject'] button[type='submit']",
    )
    ASSOCIATIONS_BTN = (By.CSS_SELECTOR, "[data-testid='datasets-associations-btn']")
    ASSOCIATIONS_LIST = (By.ID, "datasets-associations")

    def set_aggregator(self, name):
        self.select_searchable_entity(self.AGGREGATOR_SELECT, name)
        self.click(self.SET_AGGREGATOR_SUBMIT)

    def set_training_plan(self, plan_path: str):
        self.type(self.SET_PLAN_PATH_INPUT, plan_path)
        self.click(self.SET_PLAN_SUBMIT)

    def update_training_plan(self, field_name: str, field_value: str):
        self.type(self.UPDATE_PLAN_FIELD_NAME_INPUT, field_name)
        self.type(self.UPDATE_PLAN_FIELD_VALUE_INPUT, field_value)
        self.click(self.UPDATE_PLAN_SUBMIT)

    def start_training_event(self, event_name: str, participants_list_path: str = ""):
        self.type(self.START_EVENT_NAME_INPUT, event_name)
        if participants_list_path:
            self.type(self.START_EVENT_PARTICIPANTS_INPUT, participants_list_path)
        self.click(self.START_EVENT_SUBMIT)

    def close_training_event(self):
        self.click(self.CLOSE_EVENT_SUBMIT)

    def get_experiment_status(self):
        self.click(self.GET_STATUS_SUBMIT)

    def open_dataset_associations(self):
        associations = self.find(self.ASSOCIATIONS_LIST)
        self.click(self.ASSOCIATIONS_BTN)
        self.wait_for_visibility_element(associations)

    def approve_first_pending_dataset_association(self):
        self.open_dataset_associations()
        buttons = self.driver.find_elements(*self.APPROVE_DATASET_BUTTONS)
        assert buttons, "No pending dataset association to approve"
        self.ensure_element_ready(buttons[0])
        buttons[0].click()

    def reject_first_pending_dataset_association(self):
        self.open_dataset_associations()
        buttons = self.driver.find_elements(*self.REJECT_DATASET_BUTTONS)
        assert buttons, "No pending dataset association to reject"
        self.ensure_element_ready(buttons[0])
        buttons[0].click()
