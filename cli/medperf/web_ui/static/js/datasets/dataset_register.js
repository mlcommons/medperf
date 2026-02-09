function onDatasetRegisterSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Dataset Registered Successfully", seconds: 3, url: "/datasets/ui/display/" + response.dataset_id });
    } else {
        showErrorModal("Failed to Register Dataset", response);
    }
}

function registerDataset(registerButton) {
    addSpinner(registerButton);
    var form = document.getElementById("dataset-register-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#dataset-register-form input, #dataset-register-form select, #dataset-register-form textarea, #dataset-register-form button");
    ajaxRequest("/datasets/register", "POST", formData, onDatasetRegisterSuccess, "Error registering dataset:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function checkDatasetFormValidity() {
    var benchmarkEl = document.getElementById("benchmark");
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var locationEl = document.getElementById("location");
    var dataPathEl = document.getElementById("data-path");
    var labelsPathEl = document.getElementById("labels-path");
    var isValid = !!(benchmarkEl && benchmarkEl.value) && !!(nameEl && nameEl.value.trim()) && !!(descEl && descEl.value.trim()) && !!(locationEl && locationEl.value.trim()) && !!(dataPathEl && dataPathEl.value.trim()) && !!(labelsPathEl && labelsPathEl.value.trim());
    var btn = document.getElementById("register-dataset-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var btn = document.getElementById("register-dataset-btn");
    if (btn) btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, registerDataset, "register this dataset?"); });
    var form = document.getElementById("dataset-register-form");
    if (form) form.querySelectorAll("input, select, textarea").forEach(function (el) {
        el.addEventListener("change", checkDatasetFormValidity);
        el.addEventListener("keyup", checkDatasetFormValidity);
    });
    var browseData = document.getElementById("browse-data-btn");
    var browseLabels = document.getElementById("browse-labels-btn");
    if (browseData) browseData.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("data-path"); });
    if (browseLabels) browseLabels.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("labels-path"); });
    checkDatasetFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
