from selenium.webdriver.common.by import By

from ..base_page import BasePage


class RegAssetPage(BasePage):
    FORM = (By.ID, "asset-register-form")

    NAME = (By.ID, "name")
    LOCAL_RADIO = (By.ID, "local")
    REMOTE_RADIO = (By.ID, "remote")
    ASSET_URL = (By.ID, "asset-url")
    ASSET_PATH = (By.ID, "asset-path")
    BROWSE_BTN = (By.ID, "browse-asset-btn")
    REGISTER = (By.ID, "register-asset-btn")

    def register_local_asset(self, name, asset_path):
        self.type(self.NAME, name)
        self.click(self.LOCAL_RADIO)
        self.type(self.ASSET_PATH, asset_path)
        self.click(self.REGISTER)

    def register_remote_asset(self, name, asset_url):
        self.type(self.NAME, name)
        self.click(self.REMOTE_RADIO)
        self.type(self.ASSET_URL, asset_url)
        self.click(self.REGISTER)
