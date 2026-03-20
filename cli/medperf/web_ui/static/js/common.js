
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

function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function removeAlert(alertEl) {
    if (alertEl._alertTimeoutId) clearTimeout(alertEl._alertTimeoutId);
    alertEl.classList.add("display-alert-out");
    setTimeout(function () { alertEl.remove(); }, 280);
}

function clearAlerts() {
    document.querySelectorAll(".floating-alert, .display-alert").forEach(function (a) { a.remove(); });
}

function onRequestFailure(xhr, status, error, errorMessage) {
    console.log(errorMessage, error);
    console.error("Error:", xhr && xhr.responseText);
}

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

function disableElements(selector) {
    document.querySelectorAll(selector).forEach(function (el) { el.disabled = true; });
}

function enableElements(selector) {
    document.querySelectorAll(selector).forEach(function (el) { el.disabled = false; });
}

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

function markAllStagesAsComplete() {
    var list = document.getElementById("stages-list");
    if (list) list.querySelectorAll(":scope > li").forEach(function (el) { markStageAsComplete(el); });
}

var STAGE_SPINNER_CLASS = "inline-block w-5 h-5 flex-shrink-0 border-2 border-green-600 dark:border-green-400 border-t-transparent dark:border-t-transparent rounded-full animate-spin";

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

function showPanel(title) {
    var panelTitle = document.getElementById("panel-title");
    var panel = document.getElementById("panel");
    if (panelTitle) panelTitle.textContent = title;
    if (panel) { panel.style.display = ""; panel.classList.remove("hidden"); }
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

function showErrorModal(errorTitle, response) {
    var responseError = (response && response.error) || "";
    var responseStatus = (response && response.status) || "";
    var errorText = (responseError + (responseError ? "<br>" : "") + responseStatus).replace(/\n/g, "<br>");
    var modalBody = "<p id=\"error-text\" class=\"text-lg font-bold text-red-600 dark:text-red-400\">" + errorText + "</p><p class=\"text-end mt-3\"><button type=\"button\" class=\"px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 cursor-pointer\" onclick=\"reloadPage();\">Click here to reload</button></p>";
    var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 close-modal-btn\">Hide</button>";
    showModal({ title: errorTitle, body: modalBody, footer: modalFooter });
}

function showConfirmModal(clickedBtn, callback, message) {
    var modalTitle = "Confirmation Prompt";
    var modalBody = "<p id=\"confirm-text\" class=\"text-lg\">Are you sure you want to " + message + "</p>";
    var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-900 dark:text-white font-semibold close-modal-btn\">Cancel</button><button id=\"confirmation-btn\" type=\"button\" class=\"px-4 py-2 rounded-xl medperf-bg dark:bg-green-600 text-white font-semibold hover:opacity-90 close-modal-btn\">Confirm</button>";
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

function respondToPrompt(value) {
    var formData = new FormData();
    formData.append("task_name", window.taskName || "");
    formData.append("is_approved", value ? "true" : "false");
    fetch("/events", { method: "POST", body: formData });
    window.isPromptReceived = false;
    var promptText = document.getElementById("prompt-text");
    var promptContainer = document.getElementById("prompt-container");
    if (promptText) promptText.innerHTML = "";
    if (promptContainer) promptContainer.classList.add("hidden");
    streamEvents(logPanel, stagesList, currentStageElement);
}

function resumeRunningTask(formSelector) {
    const form = document.querySelector(formSelector);
    const submitBtn = document.querySelector(formSelector + ' button[type="submit"]');
    const panelTitle = document.querySelector(formSelector)?.getAttribute("data-panel-title");
    const taskName = form.querySelector('input[name="task_name"]')?.value;
    
    window.taskName = taskName || "";
    addSpinner(submitBtn);
    showPanel(panelTitle + "...");
    window.onPromptComplete = onActionSuccess(panelTitle, null);
    streamEvents(logPanel, stagesList, currentStageElement, true);
}

function reloadPage() {
    window.location.reload();
}

function getEntities(switchElement) {
    var entity_name = switchElement.getAttribute("data-entity-name");
    var mine_only = switchElement.checked;
    window.location.href = "/" + entity_name + "/ui?mine_only=" + (mine_only ? "true" : "false");
}

function onLogoutSuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Successfully Logged Out", seconds: 1, url: "/medperf_login" });
    } else {
        showErrorModal("Logout Failed", response);
    }
}

function logout() {
    ajaxRequest("/logout", "POST", null, onLogoutSuccess, "Error logging out:");
}

function showCriticalPopup(data) {
    var modalTitle = "Critical Warning";
    var modalTitleClasses = "font-bold text-red-600 dark:text-red-400";
    var modalBody = "<p id=\"warning-text\" class=\"text-lg font-bold text-red-600 dark:text-red-400\">" + (data && data.message ? data.message : "") + "</p>";
    var modalFooter = "<button id=\"acknowledge-btn\" type=\"button\" class=\"px-4 py-2 rounded-xl medperf-bg dark:bg-green-600 text-white font-semibold close-modal-btn\" onclick=\"acknowledgeWarning(this);\" data-event-id=\"" + (data && data.id ? data.id : "") + "\">Acknowledge</button>";
    var extra = function () {
        document.getElementById("acknowledge-btn");
    };
    showModal({ title: modalTitle, body: modalBody, footer: modalFooter, titleClasses: modalTitleClasses, extra_func: extra });
}

function acknowledgeWarning(ackBtn) {
    var eventId = ackBtn.getAttribute("data-event-id");
    var formData = new FormData();
    formData.append("event_id", eventId);
    fetch("/events/acknowledge_event", { method: "POST", body: formData }).catch(function () {});
}

var currentStageElement = null, logPanel, stagesList;
window.isPromptReceived = false;
window.onPromptComplete = null;

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
            showErrorModal("Something when wrong while " + panelTitle.toLowerCase(), response);
        }
    };
}

function submitActionFormWithForm(form) {
    const formData = new FormData(form);
    const panelTitle = form.getAttribute("data-panel-title") || "Running task";
    const taskName = form.querySelector('input[name="task_name"]').value;
    const submitBtn = form.querySelector('button[type="submit"]');
    const handlerName = form.getAttribute("data-success-handler");

    disableElements(".detail-container form button, .detail-container form input, .detail-container form select, .detail-container form textarea, .card button");
    addSpinner(submitBtn);
    window.taskName = taskName;
    window.onPromptComplete = (handlerName && typeof window[handlerName] === "function") ? window[handlerName] : onActionSuccess(panelTitle);
    showPanel(panelTitle + "...");
    // Open EventSource before POST so we receive the task-end event for fast (sync) tasks like submit_result
    streamEvents(logPanel, stagesList, currentStageElement);
    ajaxRequest(
        form.action,
        "POST",
        formData,
        function (response) {
            // For synchronous tasks the server returns the final result in the HTTP body; show modal from that so it always appears
            if (response && (response.status === "success" || response.status === "failed")) {
                if (typeof window.onPromptComplete === "function") {
                    window.onPromptComplete(response);
                    window.onPromptComplete = null;
                }
            }
        },
        "Error: " + panelTitle
    );
}

function submitActionForm(e) {
    e.preventDefault();
    var form = e.target;
    var msg = form.getAttribute("data-confirm-message") || "continue?";
    showConfirmModal(form, submitActionFormWithForm, msg);
}

function onDomReady() {
    applyDateFormatting();
    bindModalCloseButtons();
    if (Array.isArray(window.notifications)) window.notifications.forEach(function (n) { addNotification(n); });
    logPanel = document.getElementById("log-panel");
    stagesList = document.getElementById("stages-list");

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
            var modalBody = "<pre id=\"modal-yaml-content\" class=\"language-yaml overflow-x-auto p-4 rounded-lg bg-gray-100 dark:bg-gray-700\">" + yamlDataPrettified.replace(/</g, "&lt;") + "</pre>";
            var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl medperf-bg dark:bg-green-600 text-white font-semibold close-modal-btn\">Close</button>";
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
