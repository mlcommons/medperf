var REDIRECT_BASE = "/datasets/ui/display/";
var trainingPollingIntervalId = null;

const RUN_TRAINING_TASK_NAME = "start_training";
const CONTAINER_TASK_TRAIN = "train";
const RUNNING_TASKS_POLL_MS = 2000;
const TASK_PREPARE = "prepare";
const TASK_SET_OPERATIONAL = "dataset_set_operational";
const TASK_ASSOCIATION = "dataset_association";
const TASK_TRAINING_ASSOCIATION = "dataset_training_association";
const TASK_BENCHMARK_RUN = "run_benchmark";
const TASK_RESULT_SUBMIT = "submit_result";

function updateTrainingRunningBanner(tasks) {
    var banner = document.getElementById("training-running-banner");
    if (!banner) return;
    var running = Array.isArray(tasks) && tasks.indexOf(CONTAINER_TASK_TRAIN) !== -1;
    if (running) {
        banner.classList.remove("hidden");
        document.querySelectorAll(".start-training-btn").forEach(function (btn) { btn.disabled = true; });
    } else {
        banner.classList.add("hidden");
        if (window.taskName !== RUN_TRAINING_TASK_NAME) {
            document.querySelectorAll(".start-training-btn").forEach(function (btn) {
                btn.disabled = false;
            });
        }
        if (trainingPollingIntervalId && window.taskName !== RUN_TRAINING_TASK_NAME) { clearInterval(trainingPollingIntervalId); trainingPollingIntervalId = null; }
    }
}

function onStartTrainingSuccess(response) {
    if (response && response.status === "started"){
        displayAlert("success", "Training worker started successfully.");
        startPollingTrainingRunningTasks();
    }
    else showErrorModal("Something went wrong while running the training", response);
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

function requestStartTraining(form) {
    var submitBtn = form.querySelector("button[type=submit]");
    if (submitBtn) addSpinner(submitBtn);
    window.onPromptComplete = onStartTrainingSuccess;
    var formData = new FormData(form);
    formData.append("task_name", RUN_TRAINING_TASK_NAME);
    disableElements(".card button");
    showPanel("Running training...");
    window.taskName = RUN_TRAINING_TASK_NAME;
    ajaxRequest(
        "/datasets/start_training",
        "POST",
        formData,
        onStartTrainingSuccess,
        "Error running training:"
    );
    streamEvents(logPanel, stagesList, currentStageElement);
}


function runBenchmarkExecution(executeBenchmarkButton) {
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
    window.taskName = TASK_BENCHMARK_RUN;
    ajaxRequest("/datasets/run", "POST", formData, onDatasetBenchmarkExecutionSuccess, "Error running benchmark execution:");
    showPanel("Running Benchmark Execution...");
    streamEvents(logPanel, stagesList, currentStageElement);
}

function onTrainSuccess(response) {
    if (response && response.status === "success"){
        updateTrainingRunningBanner([]);
        showReloadModal({ title: "Training Completed", seconds: 3 });
    }
    else showErrorModal("Something went wrong during training", response);
}

// Expose for data-success-handler on start training form
window.onStartTrainingSuccess = onStartTrainingSuccess;

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