import time
from medperf.web_ui.tests.pages.base_page import BasePage


def login(page: BasePage, url: str, email: str):
    page.open(url)

    assert "/medperf_login?redirected=true" in page.current_url
    assert "You are not logged in" in page.get_text(page.NOT_LOGGED_IN_ALERT)
    assert page.find(page.LOGIN).is_enabled() is False

    page_modal = page.find(page.PAGE_MODAL)

    assert page_modal.is_displayed() is False

    page.login(email=email)

    page.wait_for_visibility_element(page_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Confirmation Prompt"
    assert email in page.get_text(page.CONFIRM_TEXT)

    old_url = page.current_url
    page.confirm_run_task()

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Successfully Logged In"

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    assert "/benchmarks/ui" in page.current_url
    assert "Logout" in page.get_text(page.LOGOUT_BTN)


def logout(page: BasePage):
    page_modal = page.find(page.PAGE_MODAL)

    assert page_modal.is_displayed() is False

    page.click(page.LOGOUT_BTN)

    page.wait_for_visibility_element(page_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Confirmation Prompt"
    assert "logout?" in page.get_text(page.CONFIRM_TEXT)

    old_url = page.current_url
    page.confirm_run_task()

    while not page.find(page.PAGE_MODAL).is_displayed():
        time.sleep(0.2)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Successfully Logged Out"

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    current_url = page.current_url
    assert "/medperf_login" in current_url and "redirected=true" not in current_url
