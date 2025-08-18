function onDatasetRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Registered Successfully");
        timer(3, "/datasets/ui/display/"+response.dataset_id);
    }
    else{
        showErrorModal("Failed to Register Dataset", response)
    }
}

async function registerDataset(registerButton){
    addSpinner(registerButton);
    
    const formData = new FormData($("#dataset-register-form")[0]);

    disableElements("#dataset-register-form input, #dataset-register-form select, #dataset-register-form textarea, #dataset-register-form button");

    ajaxRequest(
        "/datasets/register",
        "POST",
        formData,
        onDatasetRegisterSuccess,
        "Error registering dataset:"
    );

    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkDatasetFormValidity() {
    const isValid = Boolean(
        $("#benchmark").val() &&
        $("#name").val().trim() &&
        $("#description").val().trim() &&
        $("#location").val().trim() &&
        $("#data-path").val().trim() &&
        $("#labels-path").val().trim()
    );
    $("#register-dataset-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-dataset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerDataset, "register this dataset?");
    });
    $("#dataset-register-form input, #dataset-register-form select, #dataset-register-form textarea").on("change keyup", checkDatasetFormValidity);
    
    $("#browse-data-btn").on("click", () => {
        browseWithFiles = false;
        browseFolderHandler("data-path");
    });

    $("#browse-labels-btn").on("click", () => {
        browseWithFiles = false;
        browseFolderHandler("labels-path");
    });
});