/**
 * Automatic grant access workers running for this container, by benchmark ID
 * (rendered by the server in the panel's `data-running-auto-access`).
 */
function parseRunningAutoAccess(panel) {
    if (!panel) return {};
    try {
        return JSON.parse(panel.getAttribute("data-running-auto-access") || "{}");
    } catch (_) {
        return {};
    }
}

/** ID of the benchmark selected for automatic grant access. */
function getSelectedBenchmarkId() {
    var benchmarkEl = document.getElementById("benchmark-auto");
    return benchmarkEl && benchmarkEl.value ? benchmarkEl.value : "";
}

/** The running automatic grant access of a benchmark, if any. */
function getRunningStateForBenchmark(runningAutoAccess, benchmarkId) {
    if (!benchmarkId) return null;
    return runningAutoAccess[benchmarkId] || null;
}

/** Split a space-separated emails string. */
function parseStoredEmails(emails) {
    if (!emails) return [];
    return String(emails).trim().split(/\s+/).filter(Boolean);
}

/** Show or hide an element. */
function setElementVisible(element, visible) {
    if (!element) return;
    element.style.display = visible ? "" : "none";
    element.classList.toggle("hidden", !visible);
}

/**
 * Update the automatic grant access panel for the selected benchmark:
 * its settings and Start/Stop/Logs buttons depend on whether it runs.
 */
function updateAutoAccessUI() {
    var panel = document.getElementById("auto-access-panel");
    var actionsEl = document.getElementById("auto-access-actions");
    var startBtn = document.getElementById("start-auto-access-btn");
    var stopBtn = document.getElementById("stop-auto-access-btn");
    var viewLogsBtn = document.getElementById("view-auto-access-logs-btn");
    var runningBadge = document.getElementById("running-badge");
    var intervalEl = document.getElementById("interval-auto");
    var emailContainer = document.getElementById("allowed-email-list-auto");
    var emailInput = document.getElementById("email-input-auto");
    var benchmarkId = getSelectedBenchmarkId();
    var runningAutoAccess = parseRunningAutoAccess(panel);
    var runningState = getRunningStateForBenchmark(runningAutoAccess, benchmarkId);
    var isRunning = Boolean(runningState);

    setElementVisible(startBtn, false);
    setElementVisible(stopBtn, false);
    setElementVisible(viewLogsBtn, false);
    setElementVisible(runningBadge, false);

    if (!benchmarkId) {
        setElementVisible(actionsEl, false);
        if (intervalEl) {
            intervalEl.value = "5";
            intervalEl.disabled = true;
        }
        if (emailInput) emailInput.disabled = true;
        clearEmailChips(emailContainer);
        return;
    }

    setElementVisible(actionsEl, true);

    if (isRunning) {
        if (intervalEl) {
            intervalEl.value = runningState.interval || 5;
            intervalEl.disabled = true;
        }
        if (emailInput) emailInput.disabled = true;
        setEmailChips(emailContainer, parseStoredEmails(runningState.emails));
        setElementVisible(stopBtn, true);
        setElementVisible(viewLogsBtn, true);
        setElementVisible(runningBadge, true);
    } else {
        if (intervalEl) {
            intervalEl.value = "5";
            intervalEl.disabled = false;
        }
        if (emailInput) emailInput.disabled = false;
        clearEmailChips(emailContainer);
        setElementVisible(startBtn, true);
    }
}

/** Check the grant access form before submitting it. */
function checkAccessForm() {
    if (!document.getElementById("benchmark") || !document.getElementById("benchmark").value) {
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    return true;
}

/** Check the automatic grant access settings before starting it. */
function checkAutoAccessForm() {
    if (!getSelectedBenchmarkId()) {
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    var intervalEl = document.getElementById("interval-auto");
    var interval = intervalEl ? Number(intervalEl.value) : 0;
    if (!interval || interval < 5 || interval > 60) {
        showErrorToast("Make sure that the time interval is between 5 and 60 (inclusive)");
        return false;
    }
    return true;
}

/** Warn in the confirmation message when no email filters the data owners. */
function emptyAllowListWarning(allowListArr, message) {
    if (allowListArr.length) return message;
    return message + " <strong>Note: no emails were added - this will grant access to ALL " +
        "eligible data owners, with no email filtering.</strong>";
}

/** Start granting access automatically at the chosen interval. */
function startAutoGrant(startBtn) {
    disableElements(".card button, .card input, .card select");
    var panel = document.getElementById("auto-access-panel");
    var allowListArr = getEmailsList(document.getElementById("allowed-email-list-auto"));
    var formData = new FormData();
    formData.append("benchmark_id", getSelectedBenchmarkId());
    formData.append("model_id", panel ? panel.getAttribute("data-model-id") : "");
    formData.append("interval", document.getElementById("interval-auto").value);
    formData.append("emails", allowListArr.join(" "));
    ajaxRequest("/containers/start_auto_access", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Successfully Started Auto Grant Access", seconds: 2 });
        else showErrorModal("Failed to Start Auto Grant Access", response);
    }, "Failed to start auto grant access");
}

/** Stop the automatic grant access of the selected benchmark. */
function stopAutoGrant(stopBtn) {
    disableElements(".card button, .card input, .card select");
    var panel = document.getElementById("auto-access-panel");
    var formData = new FormData();
    formData.append("model_id", panel ? panel.getAttribute("data-model-id") : "");
    formData.append("benchmark_id", getSelectedBenchmarkId());
    ajaxRequest("/containers/stop_auto_access", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Successfully Stopped Auto Grant Access", seconds: 2 });
        else showErrorModal("Failed to Stop Auto Grant Access", response);
    }, "Failed to stop auto grant access");
}

/** Show the logs of the automatic grant access of the selected benchmark. */
function viewAutoAccessLogs() {
    var panel = document.getElementById("auto-access-panel");
    var modelId = panel ? panel.getAttribute("data-model-id") : "";
    var benchmarkId = getSelectedBenchmarkId();
    var url = "/containers/auto_access_logs?model_id=" + encodeURIComponent(modelId) +
        "&benchmark_id=" + encodeURIComponent(benchmarkId);
    ajaxRequest(url, "GET", null, function (response) {
        var logs = (response && response.logs) || [];
        var body = logs.length
            ? "<pre class=\"text-sm overflow-x-auto whitespace-pre-wrap font-mono bg-muted text-ink p-4 rounded-lg max-h-[60vh] overflow-y-auto\">" +
                logs.map(function (line) { return escapeHtml(cleanMsg(line)); }).join("\n") + "</pre>"
            : "<p class=\"text-muted-fg\">No logs recorded yet.</p>";
        var footer = "<button type=\"button\" class=\"btn btn-sm btn-secondary close-modal-btn\">Close</button>";
        showModal({ title: "Automatic Grant Access Logs", body: body, footer: footer, modalClasses: "max-w-2xl" });
    }, "Failed to fetch automatic grant access logs");
}

/** Bind the page forms, email lists and buttons. */
function init() {
    parseEmails(document.getElementById("allowed-email-list"));
    bindEmailInputs();
    document.querySelectorAll("form[id$='-form']").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            if (form.id === "grant-access-form") {
                e.preventDefault();
                if (!checkAccessForm()) return;
                var benchEl = document.getElementById("benchmark");
                var emailsEl = document.getElementById("form-emails");
                if (benchEl) document.getElementById("form-benchmark-id").value = benchEl.value;
                if (emailsEl) emailsEl.value = getEmailsList(document.getElementById("allowed-email-list")).join(" ");
                showConfirmModal(form, submitActionFormWithForm, form.getAttribute("data-confirm-message") || "continue?");
            } else {
                submitActionForm(e);
            }
        });
    });

    var benchmarkAutoEl = document.getElementById("benchmark-auto");
    if (benchmarkAutoEl) benchmarkAutoEl.addEventListener("change", updateAutoAccessUI);

    var startBtn = document.getElementById("start-auto-access-btn");
    if (startBtn) startBtn.addEventListener("click", function (e) {
        if (!checkAutoAccessForm()) return;
        var allowListArr = getEmailsList(document.getElementById("allowed-email-list-auto"));
        var message = emptyAllowListWarning(allowListArr, "start automatic grant access for the selected benchmark?");
        showConfirmModal(e.currentTarget, startAutoGrant, message);
    });
    var stopBtn = document.getElementById("stop-auto-access-btn");
    if (stopBtn) stopBtn.addEventListener("click", function (e) {
        showConfirmModal(e.currentTarget, stopAutoGrant, "stop automatic grant access?");
    });
    var viewLogsBtn = document.getElementById("view-auto-access-logs-btn");
    if (viewLogsBtn) viewLogsBtn.addEventListener("click", viewAutoAccessLogs);

    updateAutoAccessUI();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
