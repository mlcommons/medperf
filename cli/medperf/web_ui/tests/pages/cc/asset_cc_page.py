from selenium.webdriver.common.by import By
from ..base_page import BasePage


class AssetCCPage(BasePage):
    """The confidential-computing section of a model or dataset detail page.

    Two backends are configured separately -- where the ciphertext lives and
    who may release the key -- and each backend's fields are namespaced by its
    own name, so the locators are built from the backend rather than fixed.
    """

    CONFIGURE_CC = (By.ID, "configure-cc")
    STORAGE_BACKEND = (By.ID, "storage_backend")
    VAULT_BACKEND = (By.ID, "vault_backend")
    BIND_PEER = (By.CSS_SELECTOR, 'input[name="bind_peer_asset"]')
    APPLY = (By.ID, "apply-cc-asset-btn")
    SYNC_POLICY = (By.ID, "sync-cc-policy-btn")

    @staticmethod
    def backend_field(prefix, backend, field):
        return (By.ID, f"{prefix}{backend}__{field}")

    @staticmethod
    def collector(party):
        return (
            By.CSS_SELECTOR,
            f'input[name="allowed_result_collectors"][value="{party}"]',
        )

    def set_checkbox(self, locator, checked):
        element = self.find(locator)
        if element.is_selected() != checked:
            # The toggle itself is sr-only, so its label is what takes a click.
            self.driver.execute_script("arguments[0].click()", element)

    def configure(self, backend, storage, vault, collectors, bind_peer=True):
        """Fills both services with one backend and applies the form.

        Each service gets its own settings: one backend can want different
        things of the two -- where a bucket is, and which key opens it."""
        self.set_checkbox(self.CONFIGURE_CC, True)

        for prefix, selector, settings in (
            ("storage_", self.STORAGE_BACKEND, storage),
            ("vault_", self.VAULT_BACKEND, vault),
        ):
            self.select_by_text(selector, backend)
            for field, value in settings.items():
                element = self.find(self.backend_field(prefix, backend, field))
                # An element off the screen takes no keys.
                self.ensure_element_ready(element)
                element.clear()
                element.send_keys(value)

        self.set_checkbox(self.BIND_PEER, bind_peer)

        for party in ("data_owner", "model_owner", "benchmark_owner"):
            self.set_checkbox(self.collector(party), party in collectors)

        self.click(self.APPLY)

    def sync_policy(self):
        self.click(self.SYNC_POLICY)
