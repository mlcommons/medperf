function onDatasetExportSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Exported Successfully");
        timer(3, "/datasets/ui/display/"+response.dataset_id);
    }
    else{
        showErrorModal("Failed to Export Dataset", response)
    }
}

async function exportDataset(exportButton){
    addSpinner(exportButton);
    
    const formData = new FormData($("#dataset-export-form")[0]);

    disableElements("#dataset-export-form input, #dataset-export-form button");

    ajaxRequest(
        "/datasets/export",
        "POST",
        formData,
        onDatasetExportSuccess,
        "Error exporting dataset:"
    );

    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkExportFormValidity() {
    const isValid = Boolean(
        $("#output-path").val().trim()
    );
    $("#export-dataset-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#export-dataset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, exportDataset, "export this dataset?");
    });
    $("#dataset-export-form input").on("change keyup", checkExportFormValidity);

    $("#browse-output-btn").on("click", () => {
        browseWithFiles = false;
        browseFolderHandler("output-path");
    });
});