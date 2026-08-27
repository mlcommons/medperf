from selenium.webdriver.common.by import By

from ..base_page import BasePage


class ModelDetailsPage(BasePage):
    HEADER = (By.CSS_SELECTOR, "[data-testid='model-header']")
    DETAILS_HEADING = (By.CSS_SELECTOR, "[data-testid='model-details-heading']")
    STATE_BADGES = (
        By.CSS_SELECTOR,
        "[data-testid='model-state'], [data-testid='model-validity']",
    )

    MODEL_ID_LABEL = (By.CSS_SELECTOR, "[data-testid='model-id-label']")
    MODEL_ID_VALUE = (By.CSS_SELECTOR, "[data-testid='model-id']")
    OWNER_LABEL = (By.CSS_SELECTOR, "[data-testid='model-owner-label']")
    OWNER_VALUE = (By.CSS_SELECTOR, "[data-testid='model-owner']")

    # Emitted by macros/model_detail_util_macro.html::container_detail_util(),
    # shared verbatim with the container detail page (same underlying macro).
    MANIFEST_LABEL = (By.CSS_SELECTOR, "[data-testid='container-manifest-label']")
    MANIFEST_YAML_BTN = (By.CSS_SELECTOR, "[data-testid='container-manifest-yaml-btn']")
    PARAMETERS_LABEL = (By.CSS_SELECTOR, "[data-testid='container-parameters-label']")
    PARAMETERS_YAML_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='container-parameters-yaml-btn']",
    )
    PARAMETERS_NA = (By.CSS_SELECTOR, "[data-testid='container-parameters-na']")
    ADDITIONAL_LABEL = (By.CSS_SELECTOR, "[data-testid='container-additional-label']")
    ADDITIONAL_LINK = (By.CSS_SELECTOR, "[data-testid='container-additional-link']")
    ADDITIONAL_NA = (By.CSS_SELECTOR, "[data-testid='container-additional-na']")

    CREATED_LABEL = (By.CSS_SELECTOR, "[data-testid='model-created-label']")
    CREATED = (By.CSS_SELECTOR, "[data-testid='model-created']")
    MODIFIED_LABEL = (By.CSS_SELECTOR, "[data-testid='model-modified-label']")
    MODIFIED = (By.CSS_SELECTOR, "[data-testid='model-modified']")

    MANAGE_ACCESS = (By.CSS_SELECTOR, "a[data-testid='manage-access']")

    ASSOCIATIONS = (By.CSS_SELECTOR, "[data-testid='benchmark-associations']")
    ASSOCIATIONS_BTN = (
        By.CSS_SELECTOR,
        "button[data-testid='benchmark-associations-btn']",
    )
    DROPDOWN_BTN = (By.ID, "associate-dropdown-btn")
    REQUEST_ASSOCIATION_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='request-bmk-association']",
    )

    ACCESS_LABEL = (By.CSS_SELECTOR, "[data-testid='model-access-label']")
    ACCESS_GRANTED = (By.CSS_SELECTOR, "[data-testid='model-access-granted']")
    ACCESS_PENDING = (By.CSS_SELECTOR, "[data-testid='model-access-pending']")

    # Emitted by macros/model_detail_util_macro.html::asset_detail_util(),
    # the non-container (asset-backed) branch's equivalent of the container-* block above.
    ASSET_LABEL = (By.CSS_SELECTOR, "[data-testid='asset-label']")
    ASSET_LINK = (By.CSS_SELECTOR, "[data-testid='asset-link']")
    ASSET_LOCAL = (By.CSS_SELECTOR, "[data-testid='asset-local']")
    ASSET_HASH_LABEL = (By.CSS_SELECTOR, "[data-testid='asset-hash-label']")
    ASSET_HASH = (By.CSS_SELECTOR, "[data-testid='asset-hash']")

    # Emitted by macros/cc_asset_macro.html::gcp_asset()
    CC_CONFIGURE_CHECKBOX = (By.ID, "configure-cc")
    CC_APPLY_BTN = (By.ID, "apply-cc-asset-btn")
    CC_SYNC_BTN = (By.ID, "sync-cc-policy-btn")

    CC_FIELDS = (
        "project_id",
        "project_number",
        "bucket",
        "keyring_name",
        "key_name",
        "key_location",
        "wip",
        "wip_provider",
    )

    def cc_field(self, name):
        return (By.ID, f"cc-{name}")

    def request_association(self):
        self.click(self.DROPDOWN_BTN)
        self.click(self.REQUEST_ASSOCIATION_BTN)

    def configure_cc(self, values: dict):
        # sr-only peer checkbox (visually hidden toggle UI, like the
        # listing "Mine only" switch) - needs a JS click, a plain
        # WebElement.click() isn't considered interactable.
        checkbox = self.find(self.CC_CONFIGURE_CHECKBOX)
        self.driver.execute_script("arguments[0].click();", checkbox)
        for field, value in values.items():
            self.type(self.cc_field(field), value)
        self.click(self.CC_APPLY_BTN)

    def sync_cc_policy(self):
        self.click(self.CC_SYNC_BTN)
