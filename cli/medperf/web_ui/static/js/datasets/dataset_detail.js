var REDIRECT_BASE = "/datasets/ui/display/";
var trainingPollingIntervalId = null;

const CONTAINER_TASK_TRAIN = "train";
const RUNNING_TASKS_POLL_MS = 2000;

function updateTrainingRunningBanner(tasks) {
    var banner = document.getElementById("training-running-banner");
    if (!banner) return;
    var running = Array.isArray(tasks) && tasks.indexOf(CONTAINER_TASK_TRAIN) !== -1;
    if (running) {
        banner.classList.remove("hidden");
    } else {
        banner.classList.add("hidden");
    }
}

function pollTrainingRunningTasks() {
    var banner = document.getElementById("training-running-banner");
    if (!banner) return;
    fetch("/api/running_tasks", { method: "GET" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data && Array.isArray(data.tasks)) updateTrainingRunningBanner(data.tasks);
        })
        .catch(function () {});
}

function startPollingTrainingRunningTasks() {
    pollTrainingRunningTasks();
    if (!trainingPollingIntervalId) trainingPollingIntervalId = setInterval(pollTrainingRunningTasks, RUNNING_TASKS_POLL_MS);
}


function onRunTrainingSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Training Ran Successfully", seconds: 3 });
    } else showErrorModal("Something went wrong while running the training", response);
}

async function submitActionFormWithForm(form) {
    var formData = new FormData(form);
    var panelTitle = form.getAttribute("data-panel-title") || "Action";
    var isRunForm = (form.getAttribute("action") || "").indexOf("/datasets/start_training") !== -1;

    disableElements(".detail-container form button, .detail-container form input, .detail-container form select");
    var submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) addSpinner(submitBtn);
    showPanel(panelTitle + "...");

    var successCallback = isRunForm ? onRunTrainingSuccess : onActionSuccess(panelTitle);
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
    if (isRunForm) startPollingTrainingRunningTasks();
}

function submitActionForm(e) {
    e.preventDefault();
    var form = e.target;
    var msg = form.getAttribute("data-confirm-message") || "continue?";
    showConfirmModal(form, submitActionFormWithForm, msg);
}

function stopTraining() {
    var btn = document.getElementById("stop-training-btn");
    btn.disabled = true;
    var formData = new FormData();
    formData.append("task_name", CONTAINER_TASK_TRAIN);
    fetch("/api/stop_task", { method: "POST", body: formData })
        .then(function (r) {
            if (r.ok) {
                updateTrainingRunningBanner([]);
                displayAlert("success", "Training stopped.");
            }
            btn.disabled = false;
        })
        .catch(function () { btn.disabled = false; });
}

async function runBenchmarkExecution(executeBenchmarkButton) {
    addSpinner(executeBenchmarkButton);
    var formData = new FormData();
    var benchmarkId = executeBenchmarkButton.getAttribute("data-benchmark-id");
    var datasetId = executeBenchmarkButton.getAttribute("data-dataset-id");
    var runAll = executeBenchmarkButton.getAttribute("data-runAll") === "true";
    if (runAll) {
        document.querySelectorAll("[id^='run-" + benchmarkId + "-']").forEach(function (button) {
            if (!button.classList.contains("hidden") && !button.classList.contains("d-none")) {
                formData.append("model_ids", button.getAttribute("data-model-id"));
                addSpinner(button);
            }
        });
    } else {
        formData.append("model_ids", executeBenchmarkButton.getAttribute("data-model-id"));
    }
    formData.append("dataset_id", datasetId);
    formData.append("benchmark_id", benchmarkId);
    formData.append("run_all", runAll);
    disableElements(".card button");
    ajaxRequest("/datasets/run", "POST", formData, onDatasetBenchmarkExecutionSuccess, "Error running benchmark execution:");
    window.taskId = await getTaskId();
    showPanel("Running Benchmark Execution...");
    streamEvents(logPanel, stagesList, currentStageElement);
}

function init() {
    document.querySelectorAll("form[id$='-form']:not(#redirect-export-form), form[id^='dataset-association-form-'], form[id^='dataset-training-association-form-'], form[id^='start-training-form-']").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    document.querySelectorAll("[id^='show-']").forEach(function (el) {
        el.addEventListener("click", function () { showResult(el); });
    });
    var exportForm = document.getElementById("redirect-export-form");
    if (exportForm) exportForm.addEventListener("submit", function (e) { e.preventDefault(); });

    var stopTrainingBtn = document.getElementById("stop-training-btn");
    if (stopTrainingBtn) stopTrainingBtn.addEventListener("click", function (e) {
        showConfirmModal(e.currentTarget, function () { stopTraining(); }, "stop the running training?");
    });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();