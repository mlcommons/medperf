
function onBenchmarkWorkflowTestSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        const nextModal = new bootstrap.Modal('#nextModal', {
            keyboard: false,
            backdrop: "static"
        })
        $("#yaml-content").html(JSON.stringify(response.results, null, 2));
        Prism.highlightElement(document.getElementById("yaml-content"));
        nextModal.show();
    }
    else{
        showErrorModal("Benchmark Workflow Test Failed", response);
    }
}

async function benchmarkWorkflowTest(workflowTestButton){
    addSpinner(workflowTestButton);

    const formData = new FormData($("#workflow-test-form")[0]);

    disableElements("#workflow-test-form input, #workflow-test-form button");

    ajaxRequest(
        "/benchmarks/run_workflow_test",
        "POST",
        formData,
        onBenchmarkWorkflowTestSuccess,
        "Error running benchmark workflow test:"
    )

    showPanel(`Running Workflow Test...`);
    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function showRegisterBenchmark(){
    window.location.href = "/benchmarks/register/ui";
}

function checkWorkflowTestFormValidity() {
    const dataPrepPath = $("#data-preparation").val().trim();
    const modelPath = $("#model-path").val().trim();
    const evaluatorPath = $("#evaluator-path").val().trim();
    const dataPath = $("#data-path").val().trim();
    const labelsPath = $("#labels-path").val().trim();
    const runTestButton = $("#run-workflow-test-btn");

    const isValid = Boolean(
        dataPrepPath.length > 0 &&
        dataPrepPath.endsWith(".yaml") &&
        modelPath.length > 0 &&
        modelPath.endsWith(".yaml") &&
        evaluatorPath.length > 0 &&
        evaluatorPath.endsWith(".yaml") &&
        dataPath.length > 0 &&
        labelsPath.length > 0
    );

    runTestButton.prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#run-workflow-test-btn").on("click", (e) => {
        benchmarkWorkflowTest(e.currentTarget);
    });
    $("#workflow-test-form input").on("keyup", checkWorkflowTestFormValidity);
});