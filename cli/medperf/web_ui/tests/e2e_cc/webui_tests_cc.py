"""The confidential-computing workflow, driven through the web UI.

A mirror of `cli/cli_tests_cc.sh`: the same three parties, the same mock CC
backends, the same chest X-ray benchmark, every step taken by clicking rather
than by calling the CLI. What it exercises that the CLI test does not is the
web UI's own plumbing -- the forms, the confirmation prompts, and the task
panel that reports a long-running command back to the browser.

Deliberately not pytest. This is a script: it runs top to bottom, prints each
step as it happens, and exits non-zero on the first failure with the browser's
last known state reported. Run it with `cli/webui_tests_cc.sh`, which builds
the test environment and starts the web UI around it.

It also records itself. The browser draws on a virtual display and ffmpeg
records that display for the whole run, captioned with the step it is on --
see `recorder.py`. A headless run is otherwise invisible.

Either operator scenario runs from here, chosen by `$CC_OPERATOR` exactly as in
`cli/tests_setup.sh`. Both release results to the data owner, so `dataowner`
collects its own results inline while `modelowner` does not collect at all --
the data owner picks them up afterwards, by clicking, with the execution id the
operator was told to hand over.
"""

import argparse
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

from medperf import config as medperf_config
from medperf.web_ui.tests.pages.base_page import BasePage
from medperf.web_ui.tests.pages.login_page import LoginPage
from medperf.web_ui.tests.pages.security_page import SecurityPage
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

BENCHMARK_OWNER = "testbo@example.com"
MODEL_OWNER = "testmo@example.com"
DATA_OWNER = "testdo@example.com"

BMK_PROFILE = "testbenchmark"
MODEL_PROFILE = "testmodel"
DATA_PROFILE = "testdata"

PREP_NAME = "cc-prep"
SCRIPT_NAME = "cc-script"
REF_MODEL_NAME = "cc-cnn-weights"
MODEL_NAME = "cc-mobilenet-weights"
BMK_NAME = "cc-bmk"
DATASET_NAME = "cc_dataset_a"

CHESTXRAY = os.path.join(REPO, "examples", "chestxray_tutorial")
CC_CHESTXRAY = os.path.join(REPO, "examples", "cc", "chestxray")

PREP = ContainerInput(
    name=PREP_NAME,
    config=os.path.join(CHESTXRAY, "data_preparator", "container_config.yaml"),
    parameters=os.path.join(CHESTXRAY, "data_preparator", "workspace", "parameters.yaml"),
)
SCRIPT = ContainerInput(
    name=SCRIPT_NAME,
    config=os.path.join(CC_CHESTXRAY, "implementation", "container_config.yaml"),
)

DEMO_URL = "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz"
CNN_URL = "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz"

CC_BACKEND = "mock"
CC_MOCK_ROOT = os.environ.get("CC_MOCK_ROOT", "/tmp/medperf_cc_mock")

# Every mock backend takes a root and nothing else.
CC_SETTINGS = {"root": CC_MOCK_ROOT}

# Both owners release results to the data owner. Who *operates* is a separate
# question, and the one this switch answers: anybody may, and when it is not
# the data owner the results are left sealed for them to collect afterwards.
COLLECTORS = ["data_owner"]

CC_OPERATOR = os.environ.get("CC_OPERATOR", "dataowner")
if CC_OPERATOR == "modelowner":
    OPERATOR_PROFILE, OPERATOR_EMAIL = MODEL_PROFILE, MODEL_OWNER
else:
    OPERATOR_PROFILE, OPERATOR_EMAIL = DATA_PROFILE, DATA_OWNER

TASK_TIMEOUT = int(os.environ.get("WEBUI_TASK_TIMEOUT", "1800"))
SHORT_WAIT = 30

# Every step names itself to this, and every waiting loop keeps that name on
# screen. It stays a no-op until main() decides there is something to record
# onto, so nothing else has to ask whether there is.
REC = NullRecorder()


class StepFailed(Exception):
    pass


class Runner:
    """Runs the steps, reports them, and stops at the first failure."""

    def __init__(self, driver, base_url, artifacts):
        self.driver = driver
        self.base_url = base_url
        self.artifacts = artifacts
        self.passed = 0
        self.failed = None
        self.started = time.time()

    def url(self, path):
        return self.base_url + path

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
        """A failure in a browser is invisible unless something records it."""
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
    """Whether an element is on screen, tolerating it being swapped out."""
    try:
        return page.driver.find_element(*locator).is_displayed()
    except WebDriverException:
        return False


def wait_for_task(page, timeout=TASK_TIMEOUT, answer=True, prompt="Confirmation Prompt"):
    """Confirms a prompted action and waits for the task to report back.

    Two different questions can appear, and conflating them is what makes this
    hang. The first is the confirmation modal, before anything runs. The second
    comes from the command itself partway through -- the web UI's equivalent of
    the CLI's `-y`, asking whether to go ahead now that it has something to
    show, such as a compatibility test's metrics. A task that is waiting on the
    second looks exactly like a task that is simply slow, so it has to be
    answered rather than waited out.

    `prompt` is the title the first one is expected to carry. Starting a
    confidential run asks its own question -- it puts a machine up in the
    operator's cloud account -- so that one is not the generic modal.
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
            # Give the click a moment to land before looking again, or the
            # same prompt is answered twice.
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
    """Lets the result modal go away, however this page chooses to do it."""
    try:
        modal = page.find(page.PAGE_MODAL)
        WebDriverWait(page.driver, SHORT_WAIT).until(EC.staleness_of(modal))
    except TimeoutException:
        page.driver.refresh()
        page.wait_for_presence_selector(page.NAVBAR)


def login(runner, email):
    page = LoginPage(runner.driver)
    page.open(runner.url("/benchmarks/ui"))

    if "/medperf_login" not in page.current_url:
        return  # already logged in on this profile

    page.login(email=email)
    wait_for_task(page)
    dismiss_task_modal(page)

    WebDriverWait(runner.driver, SHORT_WAIT).until(
        lambda d: "/medperf_login" not in d.current_url
    )


def activate_profile(runner, profile):
    page = SettingsPage(runner.driver)
    page.open(runner.url("/settings"))

    if page.get_text(page.CURRENT_PROFILE) == profile.title():
        return

    page.activate_profile(profile_name=profile.title())
    wait_for_task(page)
    dismiss_task_modal(page)

    page.open(runner.url("/settings"))
    current = page.get_text(page.CURRENT_PROFILE)
    if current != profile.title():
        raise StepFailed(f"profile is {current!r}, expected {profile.title()!r}")


def as_user(runner, profile, email):
    activate_profile(runner, profile)
    login(runner, email)


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


def configure_asset_cc(runner, entity_url):
    page = AssetCCPage(runner.driver)
    page.open(runner.url(entity_url))
    page.configure(
        backend=CC_BACKEND,
        storage=CC_SETTINGS,
        vault=CC_SETTINGS,
        collectors=COLLECTORS,
    )
    wait_for_task(page)
    dismiss_task_modal(page)

    page.open(runner.url(entity_url))
    page.sync_policy()
    wait_for_task(page)
    dismiss_task_modal(page)


def captured_detail_url(runner, fragment):
    """Where registering an entity left the browser.

    Registration redirects to the new entity's detail page, so the id comes
    from the URL rather than from searching a listing for a name -- there is no
    ambiguity and no dependence on how cards are labelled.
    """
    WebDriverWait(runner.driver, SHORT_WAIT).until(EC.url_contains(fragment))
    url = runner.driver.current_url
    return url[len(runner.base_url):] if url.startswith(runner.base_url) else url


def build_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    # Chrome will not start as root, and a small /dev/shm makes it flaky.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    # Filling the display it was given, so the recording is the browser and
    # nothing else.
    options.add_argument("--window-position=0,0")
    options.add_argument(f"--window-size={SCREEN[0]},{SCREEN[1]}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(120)
    return driver


def security_token():
    with open(medperf_config.webui_host_props) as f:
        return yaml.safe_load(f)["security_token"]


def main():
    global REC

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8200)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--headed", action="store_true",
        help="watch it live on this machine's screen, and record nothing",
    )
    parser.add_argument(
        "--artifacts",
        default=os.environ.get("WEBUI_ARTIFACTS", "/tmp/medperf_webui_cc_artifacts"),
    )
    parser.add_argument("--no-record", action="store_true", help="skip the video")
    parser.add_argument("--fps", type=int, default=int(os.environ.get("WEBUI_FPS", "10")))
    args = parser.parse_args()

    display, headless = open_display(args, parser)
    base_url = f"http://{args.host}:{args.port}"
    driver = build_driver(headless=headless)
    runner = Runner(driver, base_url, args.artifacts)

    if display:
        REC = Recorder(
            driver, display, os.path.join(args.artifacts, "run.mp4"), fps=args.fps
        )
        REC.start()

    try:
        run_workflow(runner)
    finally:
        # Stopped before the browser goes: the last thing that happened should
        # be in the video rather than the moment it disappeared.
        video = REC.stop()
        driver.quit()
        if display:
            display.stop()

    if video:
        print(f"\nvideo: {video}", flush=True)
    return runner.report()


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


def run_workflow(runner):
    state = {}

    # ---------------------------------------------------------------- setup
    def unlock():
        page = SecurityPage(runner.driver)
        page.driver.get(runner.url(f"/security_check?token={security_token()}"))
        WebDriverWait(runner.driver, SHORT_WAIT).until(
            lambda d: "/security_check" not in d.current_url
        )

    runner.step("Unlock the web UI with its security token", unlock)

    # cli_tests_cc.sh logs all three in up front, so each profile carries its
    # own credentials for the rest of the run.
    for profile, email in (
        (BMK_PROFILE, BENCHMARK_OWNER),
        (MODEL_PROFILE, MODEL_OWNER),
        (DATA_PROFILE, DATA_OWNER),
    ):
        runner.step(
            f"Login {profile}",
            lambda p=profile, e=email: as_user(runner, p, e),
        )

    # ------------------------------------------------------- benchmark owner
    runner.step(
        "Activate benchmarkowner profile",
        lambda: as_user(runner, BMK_PROFILE, BENCHMARK_OWNER),
    )
    runner.step(
        "Submit data preparation container",
        lambda: register_container(runner, PREP),
    )
    runner.step(
        "Submit benchmark script container",
        lambda: register_container(runner, SCRIPT),
    )
    runner.step(
        "Submit the reference model asset",
        lambda: register_asset(runner, REF_MODEL_NAME, url=CNN_URL),
    )

    def submit_benchmark():
        page = RegBenchmarkPage(runner.driver)
        page.open(runner.url("/benchmarks/register/ui"))
        page.register_benchmark(
            name=BMK_NAME,
            description="CC-benchmark-test",
            reference_dataset=DEMO_URL,
            data_preparator=PREP_NAME,
            reference_model=REF_MODEL_NAME,
            metrics=None,
            benchmark_script=SCRIPT_NAME,
            topology="end_to_end_script",
        )
        wait_for_task(page)
        dismiss_task_modal(page)
        state["bmk_url"] = captured_detail_url(runner, "/benchmarks/ui/display/")

    runner.step("Submit the benchmark", submit_benchmark)

    # ----------------------------------------------------------- model owner
    runner.step(
        "Activate modelowner profile",
        lambda: as_user(runner, MODEL_PROFILE, MODEL_OWNER),
    )

    def submit_model():
        weights = os.environ["CC_MODEL_TARBALL"]
        register_asset(runner, MODEL_NAME, path=weights)
        state["model_url"] = captured_detail_url(runner, "/models/ui/display/")

    runner.step("Submit the model under test", submit_model)

    def associate_model():
        page = ContainerDetailsPage(runner.driver, MODEL_NAME, BMK_NAME)
        page.open(runner.url(state["model_url"]))
        page.request_association()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Associate the model with the benchmark", associate_model)

    def model_certificate():
        page = SettingsPage(runner.driver)
        page.open(runner.url("/settings"))
        page.get_client_certificate()
        wait_for_task(page)
        dismiss_task_modal(page)

        page.open(runner.url("/settings"))
        page.submit_certificate()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Model owner client certificate", model_certificate)

    # ------------------------------------------------------------ data owner
    runner.step(
        "Activate dataowner profile",
        lambda: as_user(runner, DATA_PROFILE, DATA_OWNER),
    )
    runner.step(
        "Data owner client certificate",
        lambda: model_certificate(),
    )

    def submit_dataset():
        page = RegDatasetPage(runner.driver)
        page.open(runner.url("/datasets/register/ui"))
        page.register_dataset(
            benchmark=BMK_NAME,
            name=DATASET_NAME,
            description="cc-mock-dataset-a",
            location="mock-location-a",
            data_path=os.environ["CC_DATA_PATH"],
            labels_path=os.environ["CC_LABELS_PATH"],
        )
        wait_for_task(page)
        dismiss_task_modal(page)
        state["dataset_url"] = captured_detail_url(runner, "/datasets/ui/display/")

    runner.step("Submit the dataset", submit_dataset)

    def prepare_dataset():
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        page.prepare_dataset()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Prepare the dataset", prepare_dataset)

    def set_operational():
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        page.set_operational()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Mark the dataset operational", set_operational)

    def associate_dataset():
        page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
        page.open(runner.url(state["dataset_url"]))
        page.request_association()
        wait_for_task(page)
        dismiss_task_modal(page)

    runner.step("Associate the dataset with the benchmark", associate_dataset)

    # --------------------------------------------------- approvals (bmk owner)
    runner.step(
        "Activate benchmarkowner profile to approve",
        lambda: as_user(runner, BMK_PROFILE, BENCHMARK_OWNER),
    )

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
    runner.step(
        "Activate modelowner profile for CC",
        lambda: as_user(runner, MODEL_PROFILE, MODEL_OWNER),
    )
    runner.step(
        "Configure the model for CC and sync its policy",
        lambda: configure_asset_cc(runner, state["model_url"]),
    )

    runner.step(
        "Activate dataowner profile for CC",
        lambda: as_user(runner, DATA_PROFILE, DATA_OWNER),
    )
    runner.step(
        "Configure the dataset for CC and sync its policy",
        lambda: configure_asset_cc(runner, state["dataset_url"]),
    )

    def cc_role(section):
        page = SettingsCCPage(runner.driver)
        page.open(runner.url("/settings"))
        page.configure(section, CC_BACKEND, CC_SETTINGS)
        wait_for_task(page)
        dismiss_task_modal(page)

    # Receiving results and running the workload are two roles, and this is
    # where they come apart: the data owner is always the collector because
    # both policies say so, while the operator is whoever $CC_OPERATOR names.
    runner.step(
        "Set up where the data owner receives results",
        lambda: cc_role("collector"),
    )
    runner.step(
        f"Activate {OPERATOR_PROFILE} profile to operate",
        lambda: as_user(runner, OPERATOR_PROFILE, OPERATOR_EMAIL),
    )
    runner.step(
        "Set up the machine the operator runs the workload on",
        lambda: cc_role("operator"),
    )

    # -------------------------------------------------------------- the run
    def run_benchmark():
        if CC_OPERATOR == "modelowner":
            page = ContainerDetailsPage(runner.driver, MODEL_NAME, BMK_NAME)
            page.open(runner.url(state["model_url"]))
            # A model owner is warned what a run costs them before it starts,
            # so their confirmation is not the generic one.
            prompt = "Confirm confidential run"
        else:
            page = DatasetDetailsPage(runner.driver, DATASET_NAME, BMK_NAME)
            page.open(runner.url(state["dataset_url"]))
            prompt = "Confirmation Prompt"
        page.run_execution()
        wait_for_task(page, prompt=prompt)
        dismiss_task_modal(page)

    runner.step(f"Run the benchmark ({CC_OPERATOR} is operator)", run_benchmark)

    # ------------------------------------------ collecting somebody else's run
    if CC_OPERATOR == "modelowner":
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

        runner.step(
            "Activate dataowner profile to collect",
            lambda: as_user(runner, DATA_PROFILE, DATA_OWNER),
        )

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
