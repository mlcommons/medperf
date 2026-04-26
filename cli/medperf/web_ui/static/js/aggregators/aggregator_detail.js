var REDIRECT_BASE = "/aggregators/ui/display/";

const RUNNING_TASKS_POLL_MS = 2000;
const AGGREGATOR_CONTAINER_TASK_NAME = "start_aggregator";
var pollingIntervalId = null;

function updateRunningBanner(tasks) {
    var banner = document.getElementById("aggregator-running-banner");
    var runCard = document.getElementById("aggregator-run-card");
    if (!banner || !runCard) return;
    var running = Array.isArray(tasks) && tasks.indexOf(AGGREGATOR_CONTAINER_TASK_NAME) !== -1;
    if (running) {
        banner.classList.remove("hidden");
        runCard.classList.add("opacity-80");
    } else {
        banner.classList.add("hidden");
        runCard.classList.remove("opacity-80");
    }
}

function pollRunningTasks() {
    fetch("/api/running_tasks", { method: "GET" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data && Array.isArray(data.tasks)) updateRunningBanner(data.tasks);
        })
        .catch(function () {});
}

function startPollingRunningTasks() {
    pollRunningTasks();
    if (!pollingIntervalId) pollingIntervalId = setInterval(pollRunningTasks, RUNNING_TASKS_POLL_MS);
}

function onGetServerCertSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Server Certificate Retrieved Successfully", seconds: 3 });
    } else {
        showErrorModal("Failed to Get Server Certificate", response);
    }
}

function onRunAggregatorSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Aggregator Ran Successfully", seconds: 3 });
    } else showErrorModal("Something went wrong while running the aggregator", response);
}

async function submitActionFormWithForm(form) {
    var formData = new FormData(form);
    var panelTitle = form.getAttribute("data-panel-title") || "Action";
    var isRunForm = (form.getAttribute("action") || "").indexOf("/aggregators/run") !== -1;

    disableElements(".detail-container form button, .detail-container form input, .detail-container form select");
    var submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) addSpinner(submitBtn);
    showPanel(panelTitle + "...");

    var successCallback = isRunForm ? onRunAggregatorSuccess : onGetServerCertSuccess;
    window.onPromptComplete = successCallback;

    ajaxRequest(
        form.action,
        "POST",
        formData,
        successCallback,
        "Error: " + panelTitle
    );
    window.taskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
    if (isRunForm) startPollingRunningTasks();
}

function submitActionForm(e) {
    e.preventDefault();
    var form = e.target;
    var msg = form.getAttribute("data-confirm-message") || "continue?";
    showConfirmModal(form, submitActionFormWithForm, msg);
}

function stopAggregator() {
    var btn = document.getElementById("stop-aggregator-btn");
    btn.disabled = true;
    var formData = new FormData();
    formData.append("task_name", AGGREGATOR_CONTAINER_TASK_NAME);
    fetch("/api/stop_task", { method: "POST", body: formData })
        .then(function (r) {
            if (r.ok) {
                updateRunningBanner([]);
                displayAlert("success", "Aggregator stopped.");
            }
            btn.disabled = false;
        })
        .catch(function () { btn.disabled = false; });
}

function init() {
    var actionForms = document.querySelectorAll('#start-aggregator-form, #get-server-cert-form');
    actionForms.forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });

    var stopBtn = document.getElementById("stop-aggregator-btn");
    if (stopBtn) stopBtn.addEventListener("click", function (e) {
        showConfirmModal(e.currentTarget, function () { stopAggregator(); }, "stop the running aggregator?");
    });

}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}