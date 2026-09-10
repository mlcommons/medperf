from selenium.webdriver.common.by import By
from ..base_page import BasePage


class SettingsCCPage(BasePage):
    """The two confidential-computing roles on the settings page.

    Operating a workload and receiving its results are separate settings
    because they are separate roles, so each has its own form keyed by section
    name -- `operator` and `collector`.
    """

    @staticmethod
    def toggle(section):
        return (By.ID, f"configure-cc-{section}")

    @staticmethod
    def apply(section):
        return (By.ID, f"apply-cc-{section}-btn")

    @staticmethod
    def container(section):
        return (By.ID, f"edit-cc-{section}-container")

    @staticmethod
    def backend_select(section):
        return (By.CSS_SELECTOR, f'#edit-cc-{section}-fields select[name="backend"]')

    @staticmethod
    def backend_field(section, backend, field):
        return (
            By.CSS_SELECTOR,
            f'#edit-cc-{section}-fields input[name="{backend}__{field}"]',
        )

    def set_checkbox(self, locator, checked):
        element = self.find(locator)
        if element.is_selected() != checked:
            self.driver.execute_script("arguments[0].click()", element)

    def configure(self, section, backend, settings):
        self.set_checkbox(self.toggle(section), True)
        self.select_by_text(self.backend_select(section), backend)

        for field, value in settings.items():
            element = self.find(self.backend_field(section, backend, field))
            # An element off the screen takes no keys.
            self.ensure_element_ready(element)
            element.clear()
            element.send_keys(value)

        self.click(self.apply(section))
