"""The safety benchmark, run confidentially on Google Cloud, through the web UI.

The safety counterpart of `webui_tests_cc_gcp.py`: the same three parties, the
same three web UIs, the same recorder -- with the AILuminate-shaped safety
benchmark in place of the chest X-ray one, and with the two halves of a
confidential run held by different people.

Two things differ from the chest X-ray run, and both are the point of this one:

- **The model owner operates and the data owner collects.** Both asset policies
  release results to `data_owner` only, and the model owner is the party who
  starts the VM. The operator therefore cannot read what their own machine
  produced: their run ends with the execution id and an instruction to hand it
  over. The data owner types that id into **Collect results** on their dataset
  page and submits what comes back. `webui_tests_cc.py` drives the same shape
  against the mock backends under `CC_OPERATOR=modelowner`.
- **Compatibility tests are skipped at benchmark registration.** The script
  container relays a run from a benchmark service and MedPerf gives a
  local-medium run no network, so a compatibility test cannot pass. The flag is
  recorded on the benchmark, so it also skips the test at both association
  steps.

`cli/webui_tests_cc_safety_gcp.sh` builds all of this and describes the parties
to this script in the JSON file named by `$WEBUI_PARTIES`. Like the other runs,
it records itself onto a virtual display -- see `recorder.py`.

Everything around a run -- the cloud resources, the server, what to check
afterwards -- is `RECIPE_gcp_safety.md`.
"""

import argparse
import json
import os
import sys
import time
import traceback

import yaml
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from medperf.web_ui.tests.pages.login_page import LoginPage
from medperf.web_ui.tests.pages.settings_page import SettingsPage
from medperf.web_ui.tests.pages.asset.register_page import RegAssetPage
from medperf.web_ui.tests.pages.benchmark.details_page import BenchmarkDetailsPage
from medperf.web_ui.tests.pages.benchmark.register_page import RegBenchmarkPage
from medperf.web_ui.tests.pages.cc.asset_cc_page import AssetCCPage
from medperf.web_ui.tests.pages.cc.settings_cc_page import SettingsCCPage
from medperf.web_ui.tests.pages.container.details_page import ContainerDetailsPage
from medperf.web_ui.tests.pages.container.register_page import RegContainerPage
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage
from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage
from medperf.web_ui.tests.config import ContainerInput
from medperf.web_ui.tests.e2e_cc.recorder import (
    SCREEN,
    NullRecorder,
    Recorder,
    VirtualDisplay,
)

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

BENCHMARK = "benchmark"
MODEL = "model"
DATA = "data"

PREP_NAME = "safety-prep"
SCRIPT_NAME = "safety-script"
REF_MODEL_NAME = "safety-reference-model"
MODEL_NAME = "safety-model-under-test"
BMK_NAME = "safety-bmk"
DATASET_NAME = "safety_service"

SAFETY = os.path.join(REPO, "examples", "safety_benchmark")

# Staged copies, so the shell script can point them at a registry of its own
# without editing the repository. Unset, the committed configs are used.
PREP_CONFIG = os.environ.get(
    "SAFETY_PREP_CONFIG", os.path.join(SAFETY, "prep", "container_config.yaml")
)
SCRIPT_CONFIG = os.environ.get(
    "SAFETY_SCRIPT_CONFIG", os.path.join(SAFETY, "container_config.yaml")
)

PREP = ContainerInput(
    name=PREP_NAME,
    config=PREP_CONFIG,
    # The service's own test mode: a handful of prompts, one per hazard.
    parameters=os.path.join(SAFETY, "prep", "workspace", "parameters_test.yaml"),
)
SCRIPT = ContainerInput(
    name=SCRIPT_NAME,
    config=SCRIPT_CONFIG,
)

# Served by the shell script. The reference model has to be a URL: a
# local-path asset is what makes an asset require CC.
MODEL_URL = os.environ.get("SAFETY_MODEL_URL", "")
DEMO_URL = os.environ.get("SAFETY_DEMO_URL", "")

# `mock` smoke tests everything but the cloud, and proves nothing about GCP.
CC_BACKEND = os.environ.get("MPCC_BACKEND", "gcp")

# Both owners release results to the data owner -- and only to them. Naming two
# would be refused: results are encrypted for one key.
COLLECTORS = ["data_owner"]

# The model owner operates, the data owner collects.
OPERATOR = MODEL
COLLECTOR = DATA

# A confidential VM has to boot, pull the workload image and run it, and this
# workload answers a benchmark service's prompts with a language model. On CPU
# that is a long way past the chest X-ray run's ninety minutes, so the ceiling
# here is three hours. Report what it actually took.
TASK_TIMEOUT = int(os.environ.get("WEBUI_TASK_TIMEOUT", "10800"))
SHORT_WAIT = 30

REC = NullRecorder()


class StepFailed(Exception):
    pass


class Party:
    """One party's web UI: where it is, and what unlocks it."""

    def __init__(self, name, spec):
        self.name = name
        self.email = spec["email"]
        self.base_url = f"http://127.0.0.1:{spec['port']}"
        self.host_props = os.path.join(spec["config_storage"], ".webui_host_props")

    @property
    def token(self):
        with open(self.host_props) as f:
            return yaml.safe_load(f)["security_token"]


def load_parties(path):
    with open(path) as f:
        described = json.load(f)
    return {name: Party(name, spec) for name, spec in described.items()}


class Runner:
    """Runs the steps, reports them, and stops at the first failure."""

    def __init__(self, driver, artifacts):
        self.driver = driver
        self.artifacts = artifacts
        self.party = None
        self.passed = 0
        self.failed = None
        self.started = time.time()

    def url(self, path):
        return self.party.base_url + path

    def step(self, name, fn):
        if self.failed:
            return
        print(f"\n=== {name} ", flush=True)
        began = time.time()
        REC.caption(f"{self.passed + 1:02d}  {name}")
        try:
            fn()
        except Exception as error:
            self.failed = name
            took = time.time() - began
            print(f"    FAILED after {took:.1f}s: {type(error).__name__}: {error}", flush=True)
            REC.caption(f"{self.passed + 1:02d}  {name} -- FAILED")
            self._capture(name)
            traceback.print_exc()
        else:
            self.passed += 1
            print(f"    ok ({time.time() - began:.1f}s)", flush=True)

    def _capture(self, name):
        slug = "".join(c if c.isalnum() else "_" for c in name)[:60]
        try:
            os.makedirs(self.artifacts, exist_ok=True)
            shot = os.path.join(self.artifacts, f"{slug}.png")
            self.driver.save_screenshot(shot)
            html = os.path.join(self.artifacts, f"{slug}.html")
            with open(html, "w") as f:
                f.write(self.driver.page_source)
            print(f"    url  : {self.driver.current_url}", flush=True)
            print(f"    shot : {shot}", flush=True)
            print(f"    html : {html}", flush=True)
        except WebDriverException as error:
            print(f"    (could not capture page state: {error})", flush=True)

    def report(self):
        took = time.time() - self.started
        print("\n" + "=" * 60, flush=True)
        if self.failed:
            print(f"FAILED at: {self.failed}", flush=True)
            print(f"{self.passed} steps passed before it, {took:.0f}s elapsed", flush=True)
            return 1
        print(f"PASSED: {self.passed} steps in {took:.0f}s", flush=True)
        return 0


def displayed(page, locator):
    try:
        return page.driver.find_element(*locator).is_displayed()
    except WebDriverException:
        return False


def wait_for_task(page, timeout=TASK_TIMEOUT, answer=True, prompt="Confirmation Prompt"):
    """Confirms a prompted action and waits for the task to report back.

    Two different questions can appear, and conflating them is what makes this
    hang -- see the mock script for the whole of it. The second one is the web
    UI's equivalent of the CLI's `-y`, and has to be answered rather than
    waited out.

    `prompt` is the title the first one is expected to carry. Starting a
    confidential run from the model page asks its own question -- it puts a
    machine up in the operator's cloud account, and warns them they may never
    see what it produces -- so that one is not the generic modal.
    """
    modal = page.find(page.PAGE_MODAL)
    WebDriverWait(page.driver, SHORT_WAIT).until(EC.visibility_of(modal))

    title = page.get_text(page.PAGE_MODAL_TITLE)
    if title != prompt:
        raise StepFailed(f"expected {prompt!r}, got {title!r}")

    page.confirm_run_task()

    deadline = time.time() + timeout
    while time.time() < deadline:
        REC.tick()
        page.follow_logs()
        if displayed(page, page.PAGE_MODAL):
            break
        if displayed(page, page.PROMPT_CONTAINER):
            page.click(page.RESPOND_YES if answer else page.RESPOND_NO)
            time.sleep(1)
        time.sleep(0.3)
    else:
        raise StepFailed(f"task did not finish within {timeout}s")

    title = page.get_text(page.PAGE_MODAL_TITLE)
    lowered = title.lower()
    if "fail" in lowered or "error" in lowered:
        detail = ""
        try:
            detail = page.get_text(page.ERROR_TEXT)
        except Exception:
            pass
        raise StepFailed(f"{title}: {detail}")

    return title


def dismiss_task_modal(page):
    try:
        modal = page.find(page.PAGE_MODAL)
        WebDriverWait(page.driver, SHORT_WAIT).until(EC.staleness_of(modal))
    except TimeoutException:
        page.driver.refresh()
        page.wait_for_presence_selector(page.NAVBAR)


def as_party(runner, party):
    """Points the browser at one party's web UI and unlocks it.

    Unlocking every time rather than once: the three UIs share a host, cookies
    are not scoped by port, and each has a security token of its own -- so the
    last party to unlock is the only one whose cookie is valid."""
    runner.party = party
    runner.driver.get(runner.url(f"/security_check?token={party.token}"))
    WebDriverWait(runner.driver, SHORT_WAIT).until(
        lambda d: "/security_check" not in d.current_url
    )


def login(runner):
    page = LoginPage(runner.driver)
    page.open(runner.url("/benchmarks/ui"))

    if "/medperf_login" not in page.current_url:
        return  # already logged in on this instance

    page.login(email=runner.party.email)
    wait_for_task(page)
    dismiss_task_modal(page)

    WebDriverWait(runner.driver, SHORT_WAIT).until(
        lambda d: "/medperf_login" not in d.current_url
    )


def register_container(runner, container):
    page = RegContainerPage(runner.driver)
    page.open(runner.url("/containers/register/ui"))
    page.register_container(container=container)
    wait_for_task(page)
    dismiss_task_modal(page)


def register_asset(runner, name, url="", path=""):
    page = RegAssetPage(runner.driver)
    page.open(runner.url("/assets/register/ui"))
    page.register_asset(name=name, url=url, path=path)
    wait_for_task(page)
    dismiss_task_modal(page)


def configure_asset_cc(runner, entity_url, storage, vault):
    page = AssetCCPage(runner.driver)
    page.open(runner.url(entity_url))
    page.configure(
        backend=CC_BACKEND, storage=storage, vault=vault, collectors=COLLECTORS
    )
    wait_for_task(page)
    dismiss_task_modal(page)

    page.open(runner.url(entity_url))
    page.sync_policy()
    wait_for_task(page)
    dismiss_task_modal(page)


def client_certificate(runner):
    page = SettingsPage(runner.driver)
    page.open(runner.url("/settings"))
    page.get_client_certificate()
    wait_for_task(page)
    dismiss_task_modal(page)

    page.open(runner.url("/settings"))
    page.submit_certificate()
    wait_for_task(page)
    dismiss_task_modal(page)


def captured_detail_url(runner, fragment):
    """Where registering an entity left the browser, without the host.

    Stored without it because entity ids come from the server and mean the same
    thing on every party's web UI."""
    WebDriverWait(runner.driver, SHORT_WAIT).until(EC.url_contains(fragment))
    url = runner.driver.current_url
    base = runner.party.base_url
    return url[len(base):] if url.startswith(base) else url


def build_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    # Filling the display it was given, so the recording is the browser and
    # nothing else. The address bar is worth keeping: it is what shows which
    # party's web UI a step is talking to.
    options.add_argument("--window-position=0,0")
    options.add_argument(f"--window-size={SCREEN[0]},{SCREEN[1]}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(120)
    return driver


def open_display(args, parser):
    """Where the browser draws, and whether that is somewhere recordable.

    Three ways to run, and the default is the one that leaves a video: a
    virtual display of its own, with ffmpeg recording it."""
    if args.headed:
        if not os.environ.get("DISPLAY"):
            parser.error("--headed needs a DISPLAY; drop it to record instead")
        return None, False
    if args.no_record:
        return None, True

    display = VirtualDisplay()
    try:
        display.start()
    except RuntimeError as error:
        print(f"Not recording: {error}", flush=True)
        return None, True
    return display, False


def cc_settings():
    """What each party puts in the confidential-computing forms.

    Every value is a cloud resource somebody created before this ran; the shell
    script passes them in, and nothing here invents one. Two asset owners means
    two of everything: separate buckets, separate keys and separate workload
    identity pools, so that neither can read the other's asset and neither's
    policy sync overwrites the other's provider.
    """
    env = os.environ

    if CC_BACKEND == "mock":
        mock = {"root": env.get("CC_MOCK_ROOT", "/tmp/medperf_cc_mock")}
        return {
            "model": (mock, mock),
            "data": (mock, mock),
            "operator": mock,
            "collector": mock,
        }

    def owner(prefix):
        storage = {
            "bucket": env[f"{prefix}_BUCKET"],
            "project_number": env["MPCC_PROJECT_NUMBER"],
            "wip": env[f"{prefix}_WIP"],
            "wip_provider": env[f"{prefix}_WIP_PROVIDER"],
        }
        vault = {
            "project_id": env["MPCC_PROJECT_ID"],
            "project_number": env["MPCC_PROJECT_NUMBER"],
            "bucket": env[f"{prefix}_BUCKET"],
            "keyring_name": env[f"{prefix}_KEYRING"],
            "key_name": env[f"{prefix}_KEY"],
            "key_location": env[f"{prefix}_KEY_LOCATION"],
            "wip": env[f"{prefix}_WIP"],
            "wip_provider": env[f"{prefix}_WIP_PROVIDER"],
        }
        return storage, vault

    return {
        "model": owner("MPCC_MODEL"),
        "data": owner("MPCC_DATA"),
        # Every field the form renders has to be filled or the button stays
        # disabled, including the one the backend would default.
        "operator": {
            "project_id": env["MPCC_PROJECT_ID"],
            "service_account_name": env["MPCC_WORKLOAD_SA_NAME"],
            "vm_name": env["MPCC_VM_NAME"],
            "vm_zone": env["MPCC_VM_ZONE"],
            "logs_poll_frequency": env.get("MPCC_LOGS_POLL_FREQUENCY", "30"),
        },
        "collector": {"bucket": env["MPCC_COLLECTOR_BUCKET"]},
    }


def main():
    global REC

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parties", default=os.environ.get("WEBUI_PARTIES"),
        help="JSON describing each party's web UI",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="watch it live on this machine's screen, and record nothing",
    )
    parser.add_argument(
        "--artifacts",
        default=os.environ.get(
            "WEBUI_ARTIFACTS", "/tmp/medperf_webui_cc_safety_gcp_artifacts"
        ),
    )
    parser.add_argument("--no-record", action="store_true", help="skip the video")
    parser.add_argument("--fps", type=int, default=int(os.environ.get("WEBUI_FPS", "10")))
    args = parser.parse_args()

    if not args.parties:
        parser.error("--parties, or $WEBUI_PARTIES, is required")
    for name, value in (("SAFETY_MODEL_URL", MODEL_URL), ("SAFETY_DEMO_URL", DEMO_URL)):
        if not value:
            parser.error(f"${name} is required -- see RECIPE_gcp_safety.md step 5")

    parties = load_parties(args.parties)
    settings = cc_settings()

    display, headless = open_display(args, parser)
    driver = build_driver(headless=headless)
    runner = Runner(driver, args.artifacts)

    if display:
        REC = Recorder(
            driver, display, os.path.join(args.artifacts, "run.mp4"), fps=args.fps
        )
        REC.start()

    try:
        run_workflow(runner, parties, settings)
    finally:
        video = REC.stop()
        driver.quit()
        if display:
            display.stop()

    if video:
        print(f"\nvideo: {video}", flush=True)
    return runner.report()


def run_workflow(runner, parties, settings):
    state = {}

    def switch(name):
        as_party(runner, parties[name])
        login(runner)

    for name in (BENCHMARK, MODEL, DATA):
        runner.step(f"Login the {name} owner", lambda n=name: switch(n))

    # ------------------------------------------------------- benchmark owner
    runner.step("Act as the benchmark owner", lambda: switch(BENCHMARK))
    runner.step(
        "Submit dataset preparation container",
        lambda: register_container(runner, PREP),
    )
    runner.step(
        "Submit benchmark script container",
        lambda: register_container(runner, SCRIPT),
    )
    runner.step(
        "Submit the reference model asset",
        lambda: register_asset(runner, REF_MODEL_NAME, url=MODEL_URL),
    )

    def submit_benchmark():
        page = RegBenchmarkPage(runner.driver)
        page.open(runner.url("/benchmarks/register/ui"))
        page.register_benchmark(
            name=BMK_NAME,
            description="AILuminate-shaped-safety-benchmark",
            reference_dataset=DEMO_URL,
            data_preparator=PREP_NAME,
            reference_model=REF_MODEL_NAME,
            metrics=None,
            benchmark_script=SCRIPT_NAME,
            topology="end_to_end_script",
            # Not optional: the run relays prompts from a benchmark service
            # and a local-medium run has no network. Recorded on the benchmark,
            # so it skips the test at both association steps too.
            skip_compatibility_tests=True,
        )
        wait_for_task(page)
        dismiss_task_modal(page)
        state["bmk_url"] = captured_detail_url(runner, "/benchmarks/ui/display/")

    runner.step("Submit the safety benchmark", submit_benchmark)

    # ----------------------------------------------------------- model owner
    runner.step("Act as the model owner", lambda: switch(MODEL))

    def submit_model():
        register_asset(runner, MODEL_NAME, path=os.environ["CC_MODEL_TARBALL"])
        state["model_url"] = captured_detail_url(runner, "/models/ui/display/")

    runner.step("Submit the model under test", submit_model)

    def associate_model():
        page = ContainerDetailsPage(runner.driver, MODEL_NAME, BMK_NAME)
        page.open(runner.url(state["model_url"]))
        page.request_association()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Associate the model with the benchmark", associate_model)
    runner.step("Model owner client certificate", lambda: client_certificate(runner))

    # ------------------------------------------------------------ data owner
    runner.step("Act as the data owner", lambda: switch(DATA))
    runner.step("Data owner client certificate", lambda: client_certificate(runner))

    def submit_dataset():
        page = RegDatasetPage(runner.driver)
        page.open(runner.url("/datasets/register/ui"))
        # The dataset is one connection.yaml: which benchmark service, and the
        # key that reaches it. There are no labels, so both paths are the same
        # folder.
        page.register_dataset(
            benchmark=BMK_NAME,
            name=DATASET_NAME,
            description="AILuminate-benchmark-service-connection",
            location="gcp-safety-location",
            data_path=os.environ["CC_DATA_PATH"],
            labels_path=os.environ["CC_LABELS_PATH"],
        )
        wait_for_task(page)
        dismiss_task_modal(page)
        state["dataset_url"] = captured_detail_url(runner, "/datasets/ui/display/")

    runner.step("Submit the service connection as a dataset", submit_dataset)

    def dataset_step(action):
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        getattr(page, action)()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Prepare the connection", lambda: dataset_step("prepare_dataset"))
    runner.step("Mark the connection operational", lambda: dataset_step("set_operational"))
    runner.step(
        "Associate the connection with the benchmark",
        lambda: dataset_step("request_association"),
    )

    # --------------------------------------------------- approvals (bmk owner)
    runner.step("Act as the benchmark owner to approve", lambda: switch(BENCHMARK))

    def approvals():
        page = BenchmarkDetailsPage(runner.driver, BMK_NAME, DATASET_NAME)
        page.open(runner.url(state["bmk_url"]))
        page.approve_dataset()
        wait_for_task(page)
        dismiss_task_modal(page)

        page = BenchmarkDetailsPage(runner.driver, BMK_NAME, MODEL_NAME)
        page.open(runner.url(state["bmk_url"]))
        page.approve_container()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Approve both associations", approvals)

    # ------------------------------------------------------- CC configuration
    runner.step("Act as the model owner for CC", lambda: switch(MODEL))
    runner.step(
        "Publish the model to the model owner's bucket and key",
        lambda: configure_asset_cc(runner, state["model_url"], *settings["model"]),
    )

    runner.step("Act as the data owner for CC", lambda: switch(DATA))
    runner.step(
        "Publish the connection to the data owner's bucket and key",
        lambda: configure_asset_cc(runner, state["dataset_url"], *settings["data"]),
    )

    def cc_role(section):
        page = SettingsCCPage(runner.driver)
        page.open(runner.url("/settings"))
        page.configure(section, CC_BACKEND, settings[section])
        wait_for_task(page)
        dismiss_task_modal(page)

    # Receiving results and running the workload are two roles, and here they
    # are held by two different people: the data owner is the collector because
    # both policies say so, and the model owner is the operator because they
    # are the one who spends the machine.
    runner.step(
        "Set up where the data owner receives results",
        lambda: cc_role("collector"),
    )
    runner.step("Act as the model owner to operate", lambda: switch(OPERATOR))
    runner.step(
        "Set up the confidential VM the model owner runs on",
        lambda: cc_role("operator"),
    )

    # -------------------------------------------------------------- the run
    def run_benchmark():
        page = ContainerDetailsPage(runner.driver, MODEL_NAME, BMK_NAME)
        page.open(runner.url(state["model_url"]))
        page.run_execution()
        # A model owner is warned what a run costs them, and that they may not
        # be the one who gets to read it, so their confirmation is not the
        # generic one.
        wait_for_task(page, prompt="Confirm confidential run")
        dismiss_task_modal(page)

    runner.step(
        "Run the safety benchmark in the confidential VM (modelowner is operator)",
        run_benchmark,
    )

    # ------------------------------------------ collecting somebody else's run
    def read_execution_id():
        """What the operator has to hand over, read off their own page.

        The results are the data owner's and the execution is the model
        owner's, so neither can see the whole of it: nothing lists this
        execution for the collector, and the operator cannot open what it
        produced. The number is the only thing that crosses.
        """
        page = ContainerDetailsPage(runner.driver, MODEL_NAME, BMK_NAME)
        page.open(runner.url(state["model_url"]))
        execution_ids = page.get_collector_execution_ids()
        if not execution_ids:
            raise StepFailed("the operator was not told which execution to hand over")
        state["execution_id"] = execution_ids[-1]
        print(f"    execution to collect: {state['execution_id']}", flush=True)

    runner.step("Read the execution the operator hands over", read_execution_id)

    runner.step("Act as the data owner to collect", lambda: switch(COLLECTOR))

    def collect_results():
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        forms = page.get_collect_forms()
        if not forms:
            raise StepFailed("the dataset page offers nothing to collect")
        page.collect_results(forms[0], state["execution_id"])
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Collect the results as the data owner", collect_results)

    def submit_result():
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        buttons = page.get_submit_buttons()
        if not buttons:
            raise StepFailed("no result to submit -- the run produced nothing")
        page.submit_result(buttons[0])
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Submit the result", submit_result)


if __name__ == "__main__":
    sys.exit(main())
