from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegAssetPage(BasePage):
    """Registering a model asset -- weights, rather than a container.

    An asset is either fetched from a URL or read from a path on this machine,
    and which one it is decides whether the run needs a confidential VM: an
    asset nobody else holds a copy of is what `requires_cc()` is about.
    """

    REG_ASSET_BTN = (By.CSS_SELECTOR, '[data-testid="reg-asset-btn"]')
    NAME = (By.ID, "name")
    LOCAL = (By.ID, "local")
    REMOTE = (By.ID, "remote")
    ASSET_URL = (By.ID, "asset-url")
    ASSET_PATH = (By.ID, "asset-path")
    REGISTER = (By.ID, "register-asset-btn")

    def register_asset(self, name, url="", path=""):
        if bool(url) == bool(path):
            raise ValueError("An asset comes from a URL or a path, not both")

        self.type(self.NAME, name)
        if url:
            self.click(self.REMOTE)
            self.type(self.ASSET_URL, url)
        else:
            self.click(self.LOCAL)
            self.type(self.ASSET_PATH, path)

        self.click(self.REGISTER)
