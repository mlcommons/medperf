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
        var submit = runCard.querySelector('form[action*="/aggregators/run"] button[type="submit"]');
        if (submit && window.taskName !== RUN_AGGREGATOR_TASK_ID) submit.disabled = false;
        if (pollingIntervalId && window.taskName !== RUN_AGGREGATOR_TASK_ID) { clearInterval(pollingIntervalId); pollingIntervalId = null; }
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

/** Task ID for event stream (matches backend active_tasks / task_id). */
const RUN_AGGREGATOR_TASK_ID = "start_aggregator";
/** Task name in running_containers (matches cube.run task=). Used for polling and stop. */
const GET_SERVER_CERT_TASK_NAME = "aggregator_get_server_cert";

function getAggregatorId(form) {
    var input = form ? form.querySelector('input[name="aggregator_id"]') : null;
    return input ? input.value : null;
}

function onGetServerCertSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Server Certificate Retrieved Successfully", seconds: 3 });
    } else {
        showErrorModal("Failed to Get Server Certificate", response);
    }
}

function onRunAggregatorSuccess(response) {
    if (response && response.status === "started") {
        displayAlert("success", "Aggregator worker started successfully.");
        startPollingRunningTasks();
    } else showErrorModal("Something went wrong while running the aggregator", response);
}

function submitActionFormWithForm(form) {
    var formData = new FormData(form);
    var panelTitle = form.getAttribute("data-panel-title") || "Action";
    var isRunForm = (form.getAttribute("action") || "").indexOf("/aggregators/run") !== -1;

    disableElements(".detail-container form button, .detail-container form input, .detail-container form select");
    var submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) addSpinner(submitBtn);
    showPanel(panelTitle + "...");

    var successCallback = isRunForm ? onRunAggregatorSuccess : onGetServerCertSuccess;
    window.onPromptComplete = successCallback;
    window.taskName = isRunForm ? RUN_AGGREGATOR_TASK_ID : GET_SERVER_CERT_TASK_NAME;

    ajaxRequest(
        form.action,
        "POST",
        formData,
        successCallback,
        "Error: " + panelTitle
    );
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