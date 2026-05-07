import datetime

from medperf.web_ui.tests.config import BASE_URL
from medperf.web_ui.tests.pages.base_page import BasePage


def switch_to_ui_mode(page: BasePage, mode: str):
    page.open(BASE_URL.format(f"/set_mode?mode={mode}"))


def parse_ui_date(date_str: str) -> datetime.datetime:
    base = date_str.split(".")[0]
    return datetime.datetime.strptime(base, "%Y-%m-%d %H:%M:%S")


def stub_event_generator(*args, **kwargs):
    yield ""
