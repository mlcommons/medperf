function onDatasetExportSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Dataset Exported Successfully", seconds: 3, url: "/datasets/ui/display/" + response.dataset_id });
    } else {
        showErrorModal("Failed to Export Dataset", response);
    }
}

function exportDataset(exportButton) {
    addSpinner(exportButton);
    var form = document.getElementById("dataset-export-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#dataset-export-form input, #dataset-export-form button");
    ajaxRequest("/datasets/export", "POST", formData, onDatasetExportSuccess, "Error exporting dataset:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function checkExportFormValidity() {
    var outputPathEl = document.getElementById("output-path");
    var isValid = !!(outputPathEl && outputPathEl.value.trim());
    var btn = document.getElementById("export-dataset-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var btn = document.getElementById("export-dataset-btn");
    if (btn) btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, exportDataset, "export this dataset?"); });
    var form = document.getElementById("dataset-export-form");
    if (form) form.querySelectorAll("input").forEach(function (el) {
        el.addEventListener("change", checkExportFormValidity);
        el.addEventListener("keyup", checkExportFormValidity);
    });
    var browseOutput = document.getElementById("browse-output-btn");
    if (browseOutput) browseOutput.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("output-path"); });
    checkExportFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
