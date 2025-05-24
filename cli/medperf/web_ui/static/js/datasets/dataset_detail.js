
function onDatasetPrepareSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Prepared Successfully");
        timer(3);
    }
    else{
        showErrorModal("Failed to Prepare Dataset", response);
    }
}

async function prepareDataset(prepareButton) {
    addSpinner(prepareButton);

    const datasetId = prepareButton.getAttribute("data-dataset-id");
    
    const formData = new FormData();
    formData.append("dataset_id", datasetId);

    disableElements(".card button");
    
    ajaxRequest(
        "/datasets/prepare",
        "POST",
        formData,
        onDatasetPrepareSuccess,
        "Error preparing dataset:"
    );

    window.runningTaskId = await getTaskId();
    showPanel(`Preparing Dataset...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetSetOperationSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Set to Operation Successfully");
        timer(3);
    }
    else{
        showErrorModal("Failed to Set Dataset to Operation", response);
    }
}

async function setDatasetToOperation(setOperationButton){
    addSpinner(setOperationButton);

    const datasetId = setOperationButton.getAttribute("data-dataset-id");
    
    const formData = new FormData();
    formData.append("dataset_id", datasetId);

    disableElements(".card button");

    ajaxRequest(
        "/datasets/set_operational",
        "POST",
        formData,
        onDatasetSetOperationSuccess,
        "Error setting dataset to operation:"
    );

    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetAssociationRequestSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Association Requested Successfully");
        timer(3);
    }
    else{
        showErrorModal("Association Request Failed", response);
    }
}

async function requestDatasetAssociation(requestAssociationButton){
    $("#dropdown-div").removeClass("show");
    addSpinner($("#associate-dropdown-btn")[0]);

    const datasetId = requestAssociationButton.getAttribute("data-dataset-id");
    const benchmarkId = requestAssociationButton.getAttribute("data-benchmark-id");

    const formData = new FormData();
    formData.append("dataset_id", datasetId);
    formData.append("benchmark_id", benchmarkId);

    disableElements(".card button");

    ajaxRequest(
        "/datasets/associate",
        "POST",
        formData,
        onDatasetAssociationRequestSuccess,
        "Error requesting dataset association:"
    );

    showPanel(`Requesting Association...`);
    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function onDatasetBenchmarkExecutionSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Execution Ran Successfully");
        timer(3);
    }
    else{
        showErrorModal("Execution Failed", response);
    }
}

async function runBenchmarkExecution(executeBenchmarkButton){
    addSpinner(executeBenchmarkButton);

    let modelIds = [];
    const formData = new FormData();

    const benchmarkId = executeBenchmarkButton.getAttribute("data-benchmark-id");
    const datasetId = executeBenchmarkButton.getAttribute("data-dataset-id");
    const runAll = executeBenchmarkButton.getAttribute("data-runAll") === "true";

    if(runAll){
        const runButtons = document.querySelectorAll(`[id^="run-${benchmarkId}-"]`);
        runButtons.forEach(button => {
            if (!button.classList.contains('d-none')) {
                modelIds.push(button.getAttribute("data-model-id"));
                addSpinner(button);
            }
        });
        modelIds.forEach(modelId => {
            formData.append("model_ids", modelId);
        });
    }
    else{
        modelIds = executeBenchmarkButton.getAttribute("data-model-id");
        formData.append("model_ids", modelIds);
        
    }

    formData.append("dataset_id", datasetId);
    formData.append("benchmark_id", benchmarkId);
    formData.append("run_all", runAll);

    disableElements(".card button");

    ajaxRequest(
        "/datasets/run",
        "POST",
        formData,
        onDatasetBenchmarkExecutionSuccess,
        "Error running benchmark execution:"
    );
        
    showPanel(`Running Benchmark Execution...`);
    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function onResultSubmitSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Results Successfully Submitted");
        timer(3);
    }
    else{
        showErrorModal("Results Submission Failed", response);
    }
}

async function submitResult(submitResultButton){
    addSpinner(submitResultButton);

    const resultId = submitResultButton.getAttribute("data-result-id");
    const benchmarkId = submitResultButton.getAttribute("data-benchmark-id");
    
    const formData = new FormData();
    formData.append("result_id", resultId);
    formData.append("benchmark_id", benchmarkId);

    disableElements(".card button");
    
    ajaxRequest(
        "/datasets/submit_result",
        "POST",
        formData,
        onResultSubmitSuccess,
        "Error submitting results:"
    );

    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function showResult(element){
    const result = JSON.parse(element.getAttribute("data-result"));

    $("#result-content").html(JSON.stringify(result, null, 2));
    $("#result-modal-title").html(`Benchmark Results`);
    const resultModal = new bootstrap.Modal('#result-modal', {
        keyboard: false,
        backdrop: "static"
    })
    resultModal.show();
    Prism.highlightElement($("#result-content")[0]);
}

$(document).ready(() => {
    $("#prepare-dataset").on("click", (e) => {
        showConfirmModal(e.currentTarget, prepareDataset, "prepare this dataset?");
    });

    $("#set-operational").on("click", (e) => {
        showConfirmModal(e.currentTarget, setDatasetToOperation, "set this dataset to operation?");
    });

    $(".request-association-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, requestDatasetAssociation, "request dataset association?");
    });

    $("[id^='run-']").on("click", (e) => {
        const targetButton = $(e.currentTarget);
        if (targetButton.hasClass("run-all-btn")){
            showConfirmModal(e.currentTarget, runBenchmarkExecution, "run the benchmark execution for all models?");
        }
        else{
            showConfirmModal(e.currentTarget, runBenchmarkExecution, "run the benchmark execution for the selected model?");
        }
        
    });

    $("[id^='show-']").on("click", (e) => {
        showResult(e.currentTarget);
    });

    $("[id^='submit-']").on("click", (e) => {
        showConfirmModal(e.currentTarget, submitResult, "submit the result?");
    });
    
    $("#redirect-export-form").off("submit");
});
