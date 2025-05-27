function onDatasetImportSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Imported Successfully");
        timer(3, "/datasets/ui/display/"+response.dataset_id);
    }
    else{
        showErrorModal("Failed to Import Dataset", response)
    }
}

async function importDataset(importButton){
    addSpinner(importButton);
    
    const formData = new FormData($("#dataset-import-form")[0]);

    disableElements("#dataset-import-form input, #dataset-import-form button");

    ajaxRequest(
        "/datasets/import",
        "POST",
        formData,
        onDatasetImportSuccess,
        "Error importing dataset:"
    );

    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkImportFormValidity() {
    var datasetIdValue = $("#dataset-id").val();
    datasetIdValue = datasetIdValue ? Number(datasetIdValue) : 0;

    const inputPathValue = $("#input-path").val().trim();
    const selectedMode = $('input[name="dataset_type"]:checked').val();
    const rawPathValue = $("#raw-path").val().trim();

    let isValid = false;

    if (datasetIdValue > 0 && inputPathValue) {
        if (selectedMode === "development") {
            isValid = Boolean(rawPathValue);
        }
        else if (selectedMode === "operational") {
            isValid = true;
        }
    }

    $("#import-dataset-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#import-dataset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, importDataset, "import this dataset?");
    });
    $("#dataset-import-form input").on("change keyup", checkImportFormValidity);

    $("#browse-input-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("input-path");
    });

    $("#browse-raw-btn").on("click", () => {
        browseWithFiles = false;
        browseFolderHandler("raw-path");
    });

    $("input[name='dataset_type']").on("change", (e) => {
        if (e.currentTarget.value === "development"){
            if ($("#raw-data-group").hasClass("d-none")) {
                $("#raw-data-group").removeClass("d-none");
            }
        }
        else{
            if (!$("#raw-data-group").hasClass("d-none")) {
                $("#raw-data-group").addClass("d-none");
                $("#raw-path").val("");
            }
        }
    });
});