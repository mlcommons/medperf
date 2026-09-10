from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    NAVBAR = (By.CSS_SELECTOR, "nav[data-testid='navbar']")
    USER_DROPDOWN = (By.CSS_SELECTOR, "button[data-testid='user-menu-button']")
    LOGOUT_BTN = (By.ID, "logout-btn")
    PAGE_MODAL = (By.ID, "page-modal")
    PAGE_MODAL_TITLE = (By.ID, "page-modal-title")
    CONFIRM_TEXT = (By.ID, "confirm-text")
    CONFIRM_BTN = (By.ID, "confirmation-btn")
    ERROR_TEXT = (By.ID, "error-text")
    ERROR_HIDE = (By.CSS_SELECTOR, '.modal-footer [data-bs-dismiss="modal"]')
    ERROR_RELOAD = (By.CSS_SELECTOR, '.modal-body [onclick="reloadPage();"]')
    PANEL = (By.ID, "panel")
    PROMPT_CONTAINER = (By.ID, "prompt-container")
    TEXT_CONTAINER = (By.ID, "text-content")
    RESPOND_YES = (By.ID, "respond-yes-btn")
    RESPOND_NO = (By.ID, "respond-no-btn")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def open(self, url):
        self.driver.get(url)
        self.wait_for_presence_selector(self.NAVBAR)

    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_elements(self, locator):
        return self.wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, locator):
        element = self.find(locator)
        self.ensure_element_ready(element)
        element.click()

    def type(self, locator, text):
        element = self.find(locator)
        self.ensure_element_ready(element)
        element.send_keys(text)

    def select_by_text(self, locator, text):
        select = self.find(locator)
        self.ensure_element_ready(select)
        Select(select).select_by_visible_text(text)

    def select_searchable_entity(self, hidden_input_locator, entity_name):
        hidden = self.find(hidden_input_locator)
        select = hidden.find_element(
            By.XPATH,
            "./ancestor::div[contains(@class,'searchable-select')]",
        )
        query = select.find_element(By.CSS_SELECTOR, ".searchable-select-query")
        self.ensure_element_ready(query)
        query.click()
        query.clear()
        query.send_keys(entity_name)

        def matching_option(_driver):
            for option in select.find_elements(
                By.CSS_SELECTOR, "li.searchable-select-option"
            ):
                if entity_name in option.text:
                    return option
            return None

        option = self.wait.until(matching_option)
        self.ensure_element_ready(option)
        option.click()
        self.wait.until(lambda _driver: bool(hidden.get_attribute("value")))

    # The panel starts collapsed and below the fold, so a recording of a long
    # task would otherwise show a spinner and nothing else.
    FOLLOW_LOGS = """
    var section = document.getElementById('log-panel-section');
    if (!section || section.classList.contains('hidden')) { return false; }
    var button = document.getElementById('toggle-log-panel-btn');
    if (button && button.getAttribute('aria-expanded') !== 'true') { button.click(); }
    var log = document.getElementById('log-panel');
    if (!log) { return false; }
    log.scrollTop = log.scrollHeight;
    var box = log.getBoundingClientRect();
    if (box.top < 0 || box.bottom > window.innerHeight) {
        log.scrollIntoView({block: 'center'});
    }
    return true;
    """

    def follow_logs(self):
        """Shows what a running task is printing, for whoever watches later."""
        try:
            return self.driver.execute_script(self.FOLLOW_LOGS)
        except WebDriverException:
            # Mid-navigation, or no panel on this page. Nothing to follow.
            return False

    def wait_for_presence_selector(self, locator):
        self.wait.until(EC.presence_of_element_located(locator))

    def wait_for_visibility_element(self, element):
        self.wait.until(EC.visibility_of(element))

    def wait_for_invisibility_element(self, element):
        self.wait.until(EC.invisibility_of_element(element))

    def wait_for_staleness_element(self, element):
        self.wait.until(EC.staleness_of(element))

    def wait_for_url_change(self, old_url):
        self.wait.until(EC.url_changes(old_url))

    @property
    def current_url(self):
        return self.driver.current_url

    def get_text(self, locator):
        return self.find(locator).text

    def confirm_run_task(self):
        self.click(self.CONFIRM_BTN)
        self.wait.until(EC.invisibility_of_element_located(self.CONFIRM_BTN))

    def __scroll_into_view(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'})",
            element,
        )

    def ensure_element_ready(self, element):
        if not self.is_element_in_viewport(element):
            self.__scroll_into_view(element)
            self.wait.until(lambda driver: self.is_element_in_viewport(element))
        self.wait.until(EC.element_to_be_clickable(element))

    def is_element_in_viewport(self, element):
        return self.driver.execute_script(
            "return (function(el){"
            "const rect = el.getBoundingClientRect();"
            "const inViewport = rect.top >= 0 && rect.left >= 0 "
            "&& rect.bottom <= (window.innerHeight||document.documentElement.clientHeight) "
            "&& rect.right <= (window.innerWidth||document.documentElement.clientWidth);"
            "const style = window.getComputedStyle(el);"
            "const visible = style.visibility !== 'hidden' && style.display !== 'none' && parseFloat(style.opacity)!==0;"
            "return inViewport && visible;"
            "})(arguments[0]);",
            element,
        )

    def is_prompt_received(self):
        return self.driver.execute_script("return window.isPromptReceived")

    def get_events_count(self):
        return self.driver.execute_script("return window.evSourceSpy.count")

    def is_confirmation_modal(self):
        return self.get_text(self.PAGE_MODAL_TITLE) == "Confirmation Prompt"

    def patch_event_source(self):
        return self.driver.execute_script("""
            (function(){
                window.evSourceSpy = { count: 0, messages: [] };
                const OriginalEventSource = window.EventSource;
                function PatchedEventSource(url, opts){
                    const es = new OriginalEventSource(url, opts);

                    es.addEventListener('message', function(e){
                        const ev = JSON.parse(e.data);
                        if (ev.task_id === window.runningTaskId){
                            if (ev.kind === "chunk"){ window.evSourceSpy.count += ev.length; }
                            else{ window.evSourceSpy.count++; }
                            window.evSourceSpy.messages.push(ev);
                        }
                    });

                    return es;
                }
                PatchedEventSource.prototype = OriginalEventSource.prototype;
                window.EventSource = PatchedEventSource;
            })();
            """)
