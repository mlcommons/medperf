import datetime
from unittest.mock import MagicMock

from medperf.web_ui.tests.config import BASE_URL
from medperf.web_ui.tests.pages.base_page import BasePage


def switch_to_ui_mode(page: BasePage, mode: str):
    page.open(BASE_URL.format(f"/set_mode?mode={mode}"))


def patch_medperf_session(
    mocker,
    user_id: int = 1,
    email: str = "webui-test@local",
    route_modules: tuple = (),
    with_user_object: bool = False,
    with_read_user_account: bool = True,
) -> dict:
    """Mock a logged-in medperf session for the webui test server.

    route_modules lists the `medperf.web_ui.<module>.routes` modules whose
    own `get_medperf_user_data` import also needs patching (each route module
    imports it separately, so patching `medperf.web_ui.common.get_medperf_user_data`
    alone does not cover route-level calls).
    """
    data = {"id": user_id, "email": email}

    if with_read_user_account:
        mocker.patch(
            "medperf.web_ui.common.read_user_account", return_value={"email": email}
        )
    mocker.patch("medperf.web_ui.common.get_medperf_user_data", return_value=data)
    for module in route_modules:
        mocker.patch(
            f"medperf.web_ui.{module}.routes.get_medperf_user_data", return_value=data
        )

    if with_user_object:
        user_obj = MagicMock()
        user_obj.id = user_id
        user_obj.is_cc_initialized.return_value = True
        user_obj.get_cc_config.return_value = {}
        mocker.patch(
            "medperf.web_ui.datasets.routes.get_medperf_user_object",
            return_value=user_obj,
        )

    return data


def parse_ui_date(date_str: str) -> datetime.datetime:
    base = date_str.split(".")[0]
    return datetime.datetime.strptime(base, "%Y-%m-%d %H:%M:%S")


def stub_event_generator(*args, **kwargs):
    yield ""
