import time
from medperf.web_ui.tests.pages.base_page import BasePage


def login(page: BasePage, url: str, email: str):
    page.open(url)

    assert "/medperf_login?redirected=true" in page.current_url
    assert "You are not logged in" in page.get_text(page.NOT_LOGGED_IN_ALERT)
    assert page.find(page.LOGIN).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False

    page.login(email=email)
    page.wait_for_visibility_element(confirm_modal)

    assert email in page.get_text(page.CONFIRM_TEXT)

    old_url = page.current_url
    page.confirm_run_task()

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Successfully Logged In"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/benchmarks/ui" in page.current_url
    assert "Logout" in page.get_text(page.LOGOUT_BTN)


def logout(page: BasePage):
    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False

    page.click(page.LOGOUT_BTN)
    page.wait_for_visibility_element(confirm_modal)

    old_url = page.current_url
    page.confirm_run_task()

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Successfully Logged Out"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    current_url = page.current_url
    assert "/medperf_login" in current_url and "redirected=true" not in current_url
