/*
 * Shared helpers of all the pages: dates, alerts, modals (confirmation, error,
 * reload), AJAX requests, running tasks (submitting action forms, streaming
 * their logs, answering prompts), the log panel and page initialization.
 *
 * Loaded by base.html after modal-queue.js and notifications.js.
 */

/** Format a date for display, in the user's locale and time zone. */
function formatDate(dateString) {
    var date = new Date(dateString);
    var now = new Date();
    var options = {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short"
    };
    if (date.getFullYear() !== now.getFullYear()) options.year = "numeric";
    return date.toLocaleDateString(undefined, options);
}

/** Return how long ago a date was (e.g. "5 min ago"); accepts seconds since epoch or a date string. */
function timeAgo(secondsSinceEpoch) {
    var ts = typeof secondsSinceEpoch === "number" ? secondsSinceEpoch * 1000 : new Date(secondsSinceEpoch).getTime();
    var seconds = Math.floor((Date.now() - ts) / 1000);
    if (seconds < 5) return "Just now";
    if (seconds < 60) return seconds + " sec ago";
    var minutes = Math.floor(seconds / 60);
    if (minutes < 60) return minutes + " min ago";
    var hours = Math.floor(minutes / 60);
    if (hours < 24) return hours + " hr" + (hours > 1 ? "s" : "") + " ago";
    var days = Math.floor(hours / 24);
    return days + " day" + (days > 1 ? "s" : "") + " ago";
}

/**
 * Fill the elements having a `data-date` attribute with the formatted date
 * (or its age, if `data-date-format="timeago"`).
 */
function applyDateFormatting() {
    document.querySelectorAll("[data-date]").forEach(function (el) {
        var date = el.getAttribute("data-date");
        if (!date) return;
        if (el.getAttribute("data-date-format") === "timeago") {
            el.textContent = timeAgo(date);
        } else {
            el.textContent = formatDate(date);
        }
    });
}

var DISPLAY_ALERT_AUTO_DISMISS_MS = 5000;

/**
 * Show an alert that disappears after `durationMs` (5 seconds by default).
 *
 * @param {string} type - "success", "danger", "warning" or "info".
 * @param {string} message - text of the alert.
 * @param {number} [durationMs]
 */
function displayAlert(type, message, durationMs) {
    var duration = durationMs != null ? durationMs : DISPLAY_ALERT_AUTO_DISMISS_MS;
    var classMap = {
        success: "display-alert-success",
        danger: "display-alert-danger",
        warning: "display-alert-warning",
        info: "display-alert-info"
    };
    var iconMap = {
        success: "&#10003;",
        danger: "&#9888;",
        warning: "&#9888;",
        info: "&#8505;"
    };
    var alertEl = document.createElement("div");
    alertEl.className = "display-alert pointer-events-auto " + (classMap[type] || classMap.info);
    alertEl.setAttribute("role", "alert");
    alertEl.innerHTML =
        "<span class=\"display-alert-icon\" aria-hidden=\"true\">" + (iconMap[type] || iconMap.info) + "</span>" +
        "<span class=\"display-alert-message\">" + escapeHtml(message) + "</span>" +
        "<button type=\"button\" class=\"display-alert-close\" aria-label=\"Close\">&times;</button>" +
        "<span class=\"display-alert-progress\"></span>";
    var container = document.getElementById("toast-container");
    if (!container) {
        container = document.body;
        alertEl.classList.add("display-alert-fixed");
    }
    container.appendChild(alertEl);

    var closeBtn = alertEl.querySelector(".display-alert-close");
    closeBtn.addEventListener("click", function () { removeAlert(alertEl); });

    var progressEl = alertEl.querySelector(".display-alert-progress");
    if (progressEl) {
        if (duration > 0) {
            progressEl.style.animationDuration = (duration / 1000) + "s";
        } else {
            progressEl.style.display = "none";
        }
    }

    var timeoutId = setTimeout(function () { removeAlert(alertEl); }, duration);
    alertEl._alertTimeoutId = timeoutId;
}

/** Escape a text so it can be safely inserted as HTML. */
function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/** Remove an alert with its exit animation. */
function removeAlert(alertEl) {
    if (alertEl._alertTimeoutId) clearTimeout(alertEl._alertTimeoutId);
    alertEl.classList.add("display-alert-out");
    setTimeout(function () { alertEl.remove(); }, 280);
}

/** Remove all the alerts at once. */
function clearAlerts() {
    document.querySelectorAll(".display-alert").forEach(function (a) { a.remove(); });
}

/** Log a failed AJAX request. */
function onRequestFailure(xhr, status, error, errorMessage) {
    console.log(errorMessage, error);
    console.error("Error:", xhr && xhr.responseText);
}

/**
 * Send a request and pass its JSON response to `successFunctionCallback`.
 * `requestBody` can be FormData or an object (sent as JSON).
 */
function ajaxRequest(requestUrl, requestType, requestBody, successFunctionCallback, errorMessage) {
    var opts = { method: requestType, headers: {} };
    if (requestBody instanceof FormData) {
        opts.body = requestBody;
    } else if (requestBody != null) {
        opts.body = typeof requestBody === "string" ? requestBody : JSON.stringify(requestBody);
        opts.headers["Content-Type"] = "application/json";
    }
    fetch(requestUrl, opts)
        .then(function (res) {
            var ct = res.headers.get("content-type");
            if (res.status === 204 || !ct || ct.indexOf("json") === -1) return {};
            return res.json();
        })
        .then(successFunctionCallback)
        .catch(function (err) {
            onRequestFailure(null, "error", err, errorMessage);
        });
}

/** Disable all the elements matching a selector. */
function disableElements(selector) {
    document.querySelectorAll(selector).forEach(function (el) { el.disabled = true; });
}

/** Enable all the elements matching a selector. */
function enableElements(selector) {
    document.querySelectorAll(selector).forEach(function (el) { el.disabled = false; });
}

/**
 * Show a modal counting down before reloading the page (or going to `opts.url`).
 *
 * @param {{title: string, seconds: number, url: (string|undefined)}} opts
 */
function showReloadModal(opts) {
    var title = opts.title, seconds = opts.seconds, url = opts.url || null;
    showModal({
        title: title,
        body: "<p id=\"popup-text\"></p>",
        extra_func: function () {
            timer({ seconds: seconds, url: url });
        }
    });
}

/** Countdown of the reload modal. */
function timer(opts) {
    var seconds = opts.seconds, url = opts.url || null;
    var popup = document.getElementById("popup-text");
    if (popup) popup.innerHTML = "The window will reload in <span id=\"timer\">" + seconds + "</span> ...";
    var timerInterval = setInterval(function () {
        seconds--;
        var t = document.getElementById("timer");
        if (t) t.textContent = seconds;
        if (seconds <= 0) {
            clearInterval(timerInterval);
            if (url) window.location.href = url;
            else reloadPage();
        }
    }, 1000);
}

/** Mark all the stages of the running task as completed. */
function markAllStagesAsComplete() {
    var list = document.getElementById("stages-list");
    if (list) list.querySelectorAll(":scope > li").forEach(function (el) { markStageAsComplete(el); });
}

var STAGE_SPINNER_CLASS = "inline-block w-5 h-5 flex-shrink-0 border-2 border-brand border-t-transparent dark:border-t-transparent rounded-full animate-spin";

/** Add a spinner to an element (buttons/links are also disabled). */
function addSpinner(element) {
    if (!element) return;
    var span = document.createElement("span");
    span.className = STAGE_SPINNER_CLASS;
    span.setAttribute("role", "status");
    span.setAttribute("aria-hidden", "true");
    if (element.tagName === "BUTTON" || element.tagName === "A") {
        element.disabled = true;
        element.setAttribute("aria-busy", "true");
        if (!element.classList.contains("inline-flex")) element.classList.add("inline-flex", "items-center", "justify-center", "gap-2");
        element.insertBefore(span, element.firstChild);
    } else {
        span.classList.add("ml-2");
        element.appendChild(span);
    }
}

/** Show the running task panel with the given title, and scroll to it. */
function showPanel(title) {
    var panelTitle = document.getElementById("panel-title");
    var panel = document.getElementById("panel");
    if (panelTitle) panelTitle.textContent = title;
    if (panel) { panel.style.display = ""; panel.classList.remove("hidden"); }
    collapseLogPanel();
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

/** Show an error modal with the error of a failed request/task response. */
function showErrorModal(errorTitle, response) {
    // A task stopped with a CleanExit (status "info") isn't an error,
    // e.g. the user declined a prompt: show its reason instead
    if (response && response.status === "info") {
        showInfoModal("Task stopped", response.error);
        return;
    }
    var responseError = (response && response.error) || "";
    var responseStatus = (response && response.status) || "";
    // Server errors are plain text: escape them, keeping their line breaks
    var errorText = escapeHtml(responseError + (responseError ? "\n" : "") + responseStatus).replace(/\n/g, "<br>");
    if (!errorText) errorText = "Something went wrong. Please try again.";
    var modalBody = "<p id=\"error-text\" class=\"text-lg font-bold text-danger\">" + errorText + "</p><p class=\"text-end mt-3\"><button type=\"button\" class=\"btn btn-xs btn-secondary\" onclick=\"reloadPage();\">Click here to reload</button></p>";
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-danger close-modal-btn\">Hide</button>";
    showModal({ title: errorTitle, body: modalBody, footer: modalFooter });
}

/**
 * Show an informative (non-error) message in a modal, with a way to reload the page.
 */
function showInfoModal(title, message) {
    var modalBody = "<p id=\"info-text\" class=\"text-lg font-bold text-ink\">" + escapeHtml(message || "") + "</p><p class=\"text-end mt-3\"><button type=\"button\" class=\"btn btn-xs btn-secondary\" onclick=\"reloadPage();\">Click here to reload</button></p>";
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-secondary close-modal-btn\">Hide</button>";
    showModal({ title: title, body: modalBody, footer: modalFooter });
}

/**
 * Ask the user to confirm an action; `callback(clickedBtn)` runs if confirmed.
 * `message` completes "Are you sure you want to ...".
 */
function showConfirmModal(clickedBtn, callback, message) {
    var modalTitle = "Confirmation Prompt";
    var modalBody = "<p id=\"confirm-text\" class=\"text-lg\">Are you sure you want to " + message + "</p>";
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-secondary close-modal-btn\">Cancel</button><button id=\"confirmation-btn\" type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\">Confirm</button>";
    var extra = function () {
        var confirmBtn = document.getElementById("confirmation-btn");
        if (confirmBtn) confirmBtn.addEventListener("click", function () {
            callback(clickedBtn);
            window.hidePageModal();
            window.onModalHidden();
        });
        document.querySelectorAll(".close-modal-btn").forEach(function (btn) {
            if (btn.id !== "confirmation-btn") btn.addEventListener("click", function () { window.hidePageModal(); window.onModalHidden(); });
        });
    };
    showModal({ title: modalTitle, body: modalBody, footer: modalFooter, extra_func: extra });
}

/** Return the ID of the task currently running on the server. */
async function getTaskId() {
    try {
        const response = await fetch("/current_task");

        if (!response.ok) {
            throw new Error("Network response was not ok");
        }

        const data = await response.json();
        return data.task_id;
    } catch (error) {
        console.error("Failed to get task id:", error);
        throw error;
    }
}

/**
 * Send the user's answer to the prompt of the running task, then resume
 * streaming its events.
 */
function respondToPrompt(value) {
    var formData = new FormData();
    formData.append("is_approved", value ? "true" : "false");
    fetch("/events", { method: "POST", body: formData });
    window.isPromptReceived = false;
    var promptText = document.getElementById("prompt-text");
    var promptContainer = document.getElementById("prompt-container");
    if (promptText) promptText.innerHTML = "";
    if (promptContainer) promptContainer.classList.add("hidden");
    streamEvents(logPanel, stagesList, currentStageElement);
}

/**
 * Resume showing a task that is still running when the page is (re)loaded:
 * its panel and logs (including the ones already emitted).
 */
function resumeRunningTask(formSelector) {
    const submitBtn = document.querySelector(formSelector + ' button[type="submit"]');
    const panelTitle = document.querySelector(formSelector)?.getAttribute("data-panel-title");
    
    addSpinner(submitBtn);
    showPanel(panelTitle + "...");
    window.onPromptComplete = onActionSuccess(panelTitle, null);
    streamEvents(logPanel, stagesList, currentStageElement, true);
}

// Some tasks start containers that keep running after the task itself ends
// (a training, an aggregator). Their pages poll the server to show whether
// they are still running, and can stop them.
var RUNNING_TASKS_POLL_MS = 2000;
var runningContainerPollers = {};

/**
 * Poll the containers running on the server and call `onUpdate(isRunning)`
 * with whether the container of the given task is one of them.
 */
function watchRunningContainer(taskName, onUpdate) {
    function poll() {
        fetch("/api/running_tasks", { method: "GET" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && Array.isArray(data.tasks)) onUpdate(data.tasks.indexOf(taskName) !== -1);
            })
            .catch(function () {});
    }
    poll();
    if (!runningContainerPollers[taskName]) {
        runningContainerPollers[taskName] = setInterval(poll, RUNNING_TASKS_POLL_MS);
    }
}

/**
 * Ask the server to stop the container of the given task. `button` is
 * disabled while the request runs; `onStopped` is called once it's stopped.
 */
function stopRunningContainer(taskName, button, onStopped) {
    if (button) button.disabled = true;
    var formData = new FormData();
    formData.append("task_name", taskName);
    fetch("/api/stop_task", { method: "POST", body: formData })
        .then(function (r) { if (r.ok) onStopped(); })
        .catch(function () {})
        .finally(function () { if (button) button.disabled = false; });
}

/** Reload the current page. */
function reloadPage() {
    window.location.reload();
}

/** Listing pages: reload the list with only the user's entities, or all of them. */
function getEntities(switchElement) {
    var entity_name = switchElement.getAttribute("data-entity-name");
    var mine_only = switchElement.checked;
    window.location.href = "/" + entity_name + "/ui?mine_only=" + (mine_only ? "true" : "false");
}

/** Handle the logout response. */
function onLogoutSuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Successfully Logged Out", seconds: 1, url: "/medperf_login" });
    } else {
        showErrorModal("Logout Failed", response);
    }
}

/** Log the user out. */
function logout() {
    ajaxRequest("/logout", "POST", null, onLogoutSuccess, "Error logging out:");
}

/** Show a critical warning sent by the server, which the user must acknowledge. */
function showCriticalPopup(data) {
    var modalTitle = "Critical Warning";
    var modalTitleClasses = "font-bold text-danger";
    var modalBody = "<p id=\"warning-text\" class=\"text-lg font-bold text-danger\">" + escapeHtml(data && data.message ? data.message : "") + "</p>";
    var modalFooter = "<button id=\"acknowledge-btn\" type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\" onclick=\"acknowledgeWarning(this);\" data-event-id=\"" + (data && data.id ? data.id : "") + "\">Acknowledge</button>";
    var extra = function () {
        document.getElementById("acknowledge-btn");
    };
    showModal({ title: modalTitle, body: modalBody, footer: modalFooter, titleClasses: modalTitleClasses, extra_func: extra });
}

/** Tell the server a critical warning was acknowledged, so it isn't shown again. */
function acknowledgeWarning(ackBtn) {
    var eventId = ackBtn.getAttribute("data-event-id");
    var formData = new FormData();
    formData.append("event_id", eventId);
    fetch("/events/acknowledge_event", { method: "POST", body: formData }).catch(function () {});
}

var currentStageElement = null, logPanel, stagesList;
window.isPromptReceived = false;
window.onPromptComplete = null;

var isLogPanelExpanded = false;

/** Expand or collapse the log panel of the running task. */
function setLogPanelExpanded(expanded) {
    var container = document.getElementById("log-panel-container");
    var btn = document.getElementById("toggle-log-panel-btn");
    var btnText = document.getElementById("toggle-log-panel-text");
    var icon = document.getElementById("toggle-log-panel-icon");
    if (!container || !btn || !btnText || !icon) return;

    isLogPanelExpanded = expanded;
    if (expanded) {
        container.classList.remove("log-panel-collapsed");
        btnText.textContent = "Collapse";
        icon.classList.remove("fa-chevron-down");
        icon.classList.add("fa-chevron-up");
        if (logPanel) logPanel.scrollTop = logPanel.scrollHeight;
    } else {
        container.classList.add("log-panel-collapsed");
        btnText.textContent = "Expand";
        icon.classList.remove("fa-chevron-up");
        icon.classList.add("fa-chevron-down");
    }
    btn.setAttribute("aria-expanded", expanded ? "true" : "false");
}

/** Collapse the log panel. */
function collapseLogPanel() {
    setLogPanelExpanded(false);
}

/** Expand the log panel if collapsed, collapse it otherwise. */
function toggleLogPanel() {
    setLogPanelExpanded(!isLogPanelExpanded);
}

/** Bind the expand/collapse button of the log panel (collapsed at first). */
function initializeLogPanelCollapse() {
    var btn = document.getElementById("toggle-log-panel-btn");
    if (!btn) return;
    btn.addEventListener("click", toggleLogPanel);
    collapseLogPanel();
}

/** Close the page modal when one of its `.close-modal-btn` buttons is clicked. */
function bindModalCloseButtons() {
    var footer = document.getElementById("page-modal-footer");
    if (footer) footer.addEventListener("click", function (e) {
        var btn = e.target.closest(".close-modal-btn");
        if (btn) { window.hidePageModal(); window.onModalHidden(); }
    });
}

document.body.addEventListener("click", function (e) {
    var t = e.target.closest("[data-dismiss-modal]");
    if (t) {
        var id = t.getAttribute("data-dismiss-modal");
        var m = document.getElementById(id);
        if (m) { m.classList.add("hidden"); document.body.classList.remove("overflow-hidden"); }
    }
});

/**
 * Return the default handler of an action form response: show a reload
 * modal on success (going to the created entity if any), an error otherwise.
 */
function onActionSuccess(panelTitle) {
    return function (response) {
        markAllStagesAsComplete();
        var id = response.entity_id;
        var url = id && typeof REDIRECT_BASE !== "undefined" ? REDIRECT_BASE + id : null;
        if (response.status === "success") {
            showReloadModal({
                title: panelTitle + " completed successfully",
                seconds: 3,
                url: url
            });
        } else {
            showErrorModal("Something went wrong while " + panelTitle.toLowerCase(), response);
        }
    };
}

/**
 * Submit an action form as a task: disable the forms, show the task panel
 * and stream the task logs until its response.
 *
 * The form can customize this with attributes: `data-panel-title`,
 * `data-success-handler` (name of the response handler) and
 * `data-after-submit` (name of a function called with the form once submitted).
 */
async function submitActionFormWithForm(form) {
    const formData = new FormData(form);
    const panelTitle = form.getAttribute("data-panel-title") || "Running task";
    const submitBtn = form.querySelector('button[type="submit"]');
    const handlerName = form.getAttribute("data-success-handler");

    disableElements("form button, form input, form select, form textarea, .card button");
    addSpinner(submitBtn);
    window.onPromptComplete = (handlerName && typeof window[handlerName] === "function") ? window[handlerName] : onActionSuccess(panelTitle);
    showPanel(panelTitle + "...");
    
    ajaxRequest(
        form.action,
        "POST",
        formData,
        function (response) {
            // Task responses have a status: "success", "failed" or "info"
            if (response && response.status) {
                if (typeof window.onPromptComplete === "function") {
                    window.onPromptComplete(response);
                    window.onPromptComplete = null;
                }
            }
        },
        "Error: " + panelTitle
    );
    window.taskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);

    // Optional page hook, e.g. to start polling a container the task started
    var afterSubmitName = form.getAttribute("data-after-submit");
    if (afterSubmitName && typeof window[afterSubmitName] === "function") window[afterSubmitName](form);
}

/**
 * Submit handler of the action forms: asks for confirmation (the form's
 * `data-confirm-message`), then submits the form as a task.
 */
function submitActionForm(e) {
    e.preventDefault();
    var form = e.target;
    var msg = form.getAttribute("data-confirm-message") || "continue?";
    showConfirmModal(form, submitActionFormWithForm, msg);
}

/**
 * Initialize what all the pages share: dates, modals, notifications, the log
 * panel, prompts, YAML links and the logout button.
 */
function onDomReady() {
    applyDateFormatting();
    bindModalCloseButtons();
    if (Array.isArray(window.notifications)) window.notifications.forEach(function (n) { addNotification(n); });
    logPanel = document.getElementById("log-panel");
    stagesList = document.getElementById("stages-list");
    initializeLogPanelCollapse();

    var respondNo = document.getElementById("respond-no-btn");
    var respondYes = document.getElementById("respond-yes-btn");
    if (respondNo) respondNo.addEventListener("click", function () { respondToPrompt(false); });
    if (respondYes) respondYes.addEventListener("click", function () { respondToPrompt(true); });

    document.querySelectorAll(".yaml-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            var fieldName = e.currentTarget.getAttribute("data-field");
            var yamlDataStr = e.currentTarget.getAttribute("data-yaml-data");
            var yamlData = [];
            try { yamlData = JSON.parse(yamlDataStr || "[]"); } catch (_) {}
            var yamlDataPrettified = JSON.stringify(yamlData, null, 2);
            var modalBody = "<pre id=\"modal-yaml-content\" class=\"language-json overflow-x-auto p-4 rounded-lg bg-muted\">" + yamlDataPrettified.replace(/</g, "&lt;") + "</pre>";
            var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\">Close</button>";
            var extra = function () {
                var pre = document.getElementById("modal-yaml-content");
                if (window.Prism && pre) Prism.highlightElement(pre);
            };
            showModal({ title: fieldName, body: modalBody, footer: modalFooter, modalClasses: "max-w-4xl w-full", extra_func: extra });
        });
    });

    var logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, logout, "logout?"); });

    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function (e) { e.preventDefault(); });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onDomReady);
} else {
    onDomReady();
}