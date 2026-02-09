
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

function displayAlert(type, message) {
    var classMap = {
        success: "bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200",
        danger: "bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200",
        warning: "bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200",
        info: "bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200"
    };
    var alertContainer = document.createElement("div");
    alertContainer.className = "floating-alert px-4 py-3 rounded-xl border-2 " + (classMap[type] || classMap.info) + " flex items-center justify-between gap-3 shadow-lg";
    alertContainer.setAttribute("role", "alert");
    alertContainer.innerHTML = "<span>" + message + "</span><button type=\"button\" class=\"close-alert-btn p-1 rounded hover:opacity-80\" aria-label=\"Close\">&times;</button>";
    alertContainer.querySelector(".close-alert-btn").addEventListener("click", function () { alertContainer.remove(); });
    document.body.appendChild(alertContainer);
}

function clearAlerts() {
    document.querySelectorAll(".floating-alert").forEach(function (a) { a.remove(); });
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

function addSpinner(element) {
    if (!element) return;
    var span = document.createElement("span");
    span.className = "inline-block w-5 h-5 ml-2 border-2 border-[#2e7d32] dark:border-green-500 border-t-transparent rounded-full animate-spin";
    span.setAttribute("role", "status");
    span.setAttribute("aria-hidden", "true");
    element.appendChild(span);
}

function showPanel(title) {
    var panelTitle = document.getElementById("panel-title");
    var panel = document.getElementById("panel");
    if (panelTitle) panelTitle.textContent = title;
    if (panel) { panel.style.display = ""; panel.classList.remove("hidden"); }
}

function showErrorModal(errorTitle, response) {
    var responseError = (response && response.error) || "";
    var responseStatus = (response && response.status) || "";
    var errorText = (responseError + (responseError ? "<br>" : "") + responseStatus).replace(/\n/g, "<br>");
    var modalBody = "<p id=\"error-text\" class=\"text-lg font-bold text-red-600 dark:text-red-400\">" + errorText + "</p><p class=\"text-end mt-3\"><button type=\"button\" class=\"px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500\" onclick=\"reloadPage();\">Click here to reload</button></p>";
    var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 close-modal-btn\">Hide</button>";
    showModal({ title: errorTitle, body: modalBody, footer: modalFooter });
}

function showConfirmModal(clickedBtn, callback, message) {
    var modalTitle = "Confirmation Prompt";
    var modalBody = "<p id=\"confirm-text\" class=\"text-lg\">Are you sure you want to " + message + "</p>";
    var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 close-modal-btn\">Cancel</button><button id=\"confirmation-btn\" type=\"button\" class=\"px-4 py-2 rounded-xl medperf-bg dark:bg-green-600 text-white font-semibold hover:opacity-90 close-modal-btn\">Confirm</button>";
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

function getTaskId() {
    return fetch("/current_task", { method: "GET" })
        .then(function (r) { return r.json(); })
        .then(function (data) { return data.task_id; })
        .catch(function (err) { console.error("Failed to get task id:", err); throw err; });
}

function respondToPrompt(value) {
    var formData = new FormData();
    formData.append("is_approved", value ? "true" : "false");
    fetch("/events", { method: "POST", body: formData });
    window.isPromptReceived = false;
    var promptText = document.getElementById("prompt-text");
    var promptContainer = document.getElementById("prompt-container");
    if (promptText) promptText.innerHTML = "";
    if (promptContainer) promptContainer.classList.add("hidden");
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function resumeRunningTask(buttonSelector, panelTitle, callback) {
    if (buttonSelector) {
        if (typeof buttonSelector === "string") {
            var el = document.querySelector(buttonSelector);
            if (el) addSpinner(el);
        } else if (Array.isArray(buttonSelector)) {
            buttonSelector.forEach(function (sel) {
                var el = typeof sel === "string" ? document.querySelector(sel) : sel;
                if (el) addSpinner(el);
            });
        }
    }
    if (panelTitle) showPanel(panelTitle);
    window.onPromptComplete = callback;
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement, true);
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
    getTaskId().then(function (id) { window.runningTaskId = id; });
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
