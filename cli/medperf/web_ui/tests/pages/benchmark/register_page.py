from selenium.webdriver.common.by import By
from ..base_page import BasePage


class RegBenchmarkPage(BasePage):
    REG_BMK_BTN = (By.CSS_SELECTOR, '[data-testid="reg-bmk-btn"]')
    TOPOLOGY_STEP = (By.ID, "topology-step")
    FORM = (By.ID, "benchmark-register-form")
    TOPOLOGY = (By.ID, "topology")
    TOPOLOGY_LABEL = (By.ID, "topology-label")
    CHANGE_TOPOLOGY = (By.ID, "change-topology-btn")
    NAME = (By.ID, "name")
    DESCRIPTION = (By.ID, "description")
    REF_DATASET = (By.ID, "reference-dataset-tarball-url")
    DATA_PREP = (By.ID, "data-preparation-container")
    REF_MODEL = (By.ID, "reference-model")
    METRICS = (By.ID, "evaluator-container")
    BENCHMARK_SCRIPT = (By.ID, "benchmark-script")
    SKIP_TESTS = (By.ID, "skip-tests")
    REQUIRE_TESTS = (By.ID, "noskip-tests")
    REGISTER = (By.ID, "register-benchmark-btn")

    @staticmethod
    def topology_option(topology):
        return (By.CSS_SELECTOR, f'.topology-option[data-topology="{topology}"]')

    def select_topology(self, topology):
        """Picks a topology, which is what reveals the rest of the form."""
        self.click(self.topology_option(topology))
        self.wait_for_visibility_element(self.find(self.NAME))

    def selected_topology(self):
        return self.find(self.TOPOLOGY).get_attribute("value")

    def is_field_enabled(self, locator):
        """Whether a topology-specific field takes part in the submission.

        Fields the chosen topology does not use are disabled, so they are left
        out of the form data entirely."""
        return self.find(locator).is_enabled()

    def register_benchmark(
        self,
        name,
        description,
        reference_dataset,
        data_preparator,
        reference_model,
        metrics=None,
        benchmark_script=None,
        topology="byo_inference_script",
        skip_compatibility_tests=False,
    ):
        self.select_topology(topology)

        self.type(self.NAME, name)
        self.type(self.DESCRIPTION, description)
        self.type(self.REF_DATASET, reference_dataset)

        self.select_searchable_entity(self.DATA_PREP, data_preparator)
        self.select_searchable_entity(self.REF_MODEL, reference_model)
        if metrics is not None:
            self.select_searchable_entity(self.METRICS, metrics)
        if benchmark_script is not None:
            self.select_searchable_entity(self.BENCHMARK_SCRIPT, benchmark_script)

        # Recorded on the benchmark, so it decides the association tests too,
        # not just this submission.
        self.click(self.SKIP_TESTS if skip_compatibility_tests else self.REQUIRE_TESTS)

        self.click(self.REGISTER)
