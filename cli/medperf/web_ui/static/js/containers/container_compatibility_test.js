function onContainerCompatibilityTestSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        $("next-modal-title").html("Container Compatibility Test Successful");
        const nextModal = new bootstrap.Modal('#next-modal', {
            keyboard: false,
            backdrop: "static"
        })
        $("#yaml-content").html(JSON.stringify(response.results, null, 2));
        Prism.highlightElement(document.getElementById("yaml-content"));
        nextModal.show();
    }
    else{
        showErrorModal("Model Compatibility Test Failed", response);
    }
}

async function runContainerCompatibilityTest(runCompTestButton){
    addSpinner(runCompTestButton);

    const formData = new FormData($("#container-comp-test-form")[0]);

    disableElements("#container-comp-test-form input, #container-comp-test-form select, #container-comp-test-form button");

    ajaxRequest(
        "/containers/run_compatibility_test",
        "POST",
        formData,
        onContainerCompatibilityTestSuccess,
        "Error running container compatibility test:"
    )

    showPanel(`Running Compatibility Test...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkCompTestFormValidity() {
    const containerPath = $("#container-path").val().trim();
    const runTestButton = $("#run-comp-test-btn");
    const isValid = Boolean(
        $("#benchmark").val() &&
        containerPath.length > 0 &&
        containerPath.endsWith(".yaml")
    );

    runTestButton.prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#run-comp-test-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, runContainerCompatibilityTest, "run the compatibility test?");
    });

    $("#container-comp-test-form input, #container-comp-test-form select").on("change keyup", checkCompTestFormValidity);

    $("#browse-container-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("container-path");
    });
});