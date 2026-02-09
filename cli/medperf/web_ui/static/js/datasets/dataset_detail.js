function onDatasetPrepareSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") showReloadModal({ title: "Dataset Prepared Successfully", seconds: 3 });
    else showErrorModal("Failed to Prepare Dataset", response);
}

function prepareDataset(prepareButton) {
    addSpinner(prepareButton);
    var datasetId = prepareButton.getAttribute("data-dataset-id");
    var formData = new FormData();
    formData.append("dataset_id", datasetId);
    disableElements(".card button");
    ajaxRequest("/datasets/prepare", "POST", formData, onDatasetPrepareSuccess, "Error preparing dataset:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    showPanel("Preparing Dataset...");
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetSetOperationSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") showReloadModal({ title: "Dataset Set to Operation Successfully", seconds: 3 });
    else showErrorModal("Failed to Set Dataset to Operation", response);
}

function setDatasetToOperation(setOperationButton) {
    addSpinner(setOperationButton);
    var datasetId = setOperationButton.getAttribute("data-dataset-id");
    var formData = new FormData();
    formData.append("dataset_id", datasetId);
    disableElements(".card button");
    ajaxRequest("/datasets/set_operational", "POST", formData, onDatasetSetOperationSuccess, "Error setting dataset to operation:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetAssociationRequestSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") showReloadModal({ title: "Association Requested Successfully", seconds: 3 });
    else showErrorModal("Association Request Failed", response);
}

function requestDatasetAssociation(requestAssociationButton) {
    var dropdownDiv = document.getElementById("dropdown-div");
    if (dropdownDiv) { dropdownDiv.classList.remove("show"); dropdownDiv.style.display = "none"; }
    var associateBtn = document.getElementById("associate-dropdown-btn");
    if (associateBtn) addSpinner(associateBtn);
    var datasetId = requestAssociationButton.getAttribute("data-dataset-id");
    var benchmarkId = requestAssociationButton.getAttribute("data-benchmark-id");
    var formData = new FormData();
    formData.append("dataset_id", datasetId);
    formData.append("benchmark_id", benchmarkId);
    disableElements(".card button");
    ajaxRequest("/datasets/associate", "POST", formData, onDatasetAssociationRequestSuccess, "Error requesting dataset association:");
    showPanel("Requesting Association...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetBenchmarkExecutionSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") showReloadModal({ title: "Execution Ran Successfully", seconds: 3 });
    else showErrorModal("Execution Failed", response);
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
    ajaxRequest("/datasets/run", "POST", formData, onDatasetBenchmarkExecutionSuccess, "Error running benchmark execution:");
    showPanel("Running Benchmark Execution...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function onResultSubmitSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") showReloadModal({ title: "Results Successfully Submitted", seconds: 3 });
    else showErrorModal("Results Submission Failed", response);
}

function submitResult(submitResultButton) {
    addSpinner(submitResultButton);
    var formData = new FormData();
    formData.append("result_id", submitResultButton.getAttribute("data-result-id"));
    formData.append("benchmark_id", submitResultButton.getAttribute("data-benchmark-id"));
    formData.append("dataset_id", submitResultButton.getAttribute("data-dataset-id"));
    disableElements(".card button");
    ajaxRequest("/datasets/submit_result", "POST", formData, onResultSubmitSuccess, "Error submitting results:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function init() {
    var prepareBtn = document.getElementById("prepare-dataset");
    if (prepareBtn) prepareBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, prepareDataset, "prepare this dataset?"); });
    var setOpBtn = document.getElementById("set-operational");
    if (setOpBtn) setOpBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, setDatasetToOperation, "set this dataset to operation?"); });
    document.querySelectorAll(".request-association-btn").forEach(function (btn) {
        btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, requestDatasetAssociation, "request dataset association?"); });
    });
    document.querySelectorAll("[id^='run-']").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            var target = e.currentTarget;
            var msg = target.classList.contains("run-all-btn") ? "run the benchmark execution for all models?" :
                (target.getAttribute("rerun") !== null && target.getAttribute("rerun") !== undefined) ? "rerun the benchmark execution for the selected model? This will clear previous results." : "run the benchmark execution for the selected model?";
            showConfirmModal(e.currentTarget, runBenchmarkExecution, msg);
        });
    });
    document.querySelectorAll("[id^='show-']").forEach(function (el) {
        el.addEventListener("click", function () { showResult(el); });
    });
    document.querySelectorAll("[id^='submit-']").forEach(function (btn) {
        btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, submitResult, "submit the result?"); });
    });
    var exportForm = document.getElementById("redirect-export-form");
    if (exportForm) exportForm.addEventListener("submit", function (e) { e.preventDefault(); });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
