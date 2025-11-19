from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    NAVBAR = (By.CSS_SELECTOR, "nav.navbar")
    LOGOUT_BTN = (By.ID, "logout-btn")
    CONFIRM_MODAL = (By.ID, "confirm-modal")
    CONFIRM_BTN = (By.ID, "confirmation-btn")
    POPUP_MODAL = (By.ID, "popup-modal")
    POPUP_TITLE = (By.ID, "popup-modal-title")
    ERROR_MODAL = (By.ID, "error-modal")
    ERROR_TITLE = (By.ID, "error-modal-title")
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
        self.wait.until(EC.invisibility_of_element_located(self.CONFIRM_MODAL))

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

    def patch_event_source(self):
        return self.driver.execute_script(
            """
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
            """
        )
