REDIRECT_BASE = "/datasets/ui/display/";

function checkImportFormValidity() {
    var datasetIdEl = document.getElementById("dataset-id");
    var datasetIdValue = datasetIdEl && datasetIdEl.value ? Number(datasetIdEl.value) : 0;
    var inputPathEl = document.getElementById("input-path");
    var inputPathValue = inputPathEl ? inputPathEl.value.trim() : "";
    var checked = document.querySelector('input[name="dataset_type"]:checked');
    var selectedMode = checked ? checked.value : "";
    var rawPathEl = document.getElementById("raw-path");
    var rawPathValue = rawPathEl ? rawPathEl.value.trim() : "";
    var isValid = false;
    if (datasetIdValue > 0 && inputPathValue) {
        if (selectedMode === "development") isValid = !!rawPathValue;
        else if (selectedMode === "operational") isValid = true;
    }
    var btn = document.getElementById("import-dataset-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var form = document.getElementById("dataset-import-form");
    if (form) form.querySelectorAll("input").forEach(function (el) {
        form.addEventListener("submit", submitActionForm);
        el.addEventListener("change", checkImportFormValidity);
        el.addEventListener("keyup", checkImportFormValidity);
    });
    var browseInput = document.getElementById("browse-input-btn");
    var browseRaw = document.getElementById("browse-raw-btn");
    if (browseInput) browseInput.addEventListener("click", function () { browseWithFiles = true; browseFolderHandler("input-path"); });
    if (browseRaw) browseRaw.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("raw-path"); });
    document.querySelectorAll("input[name='dataset_type']").forEach(function (radio) {
        radio.addEventListener("change", function () {
            var rawGroup = document.getElementById("raw-data-group");
            var rawPath = document.getElementById("raw-path");
            if (this.value === "development") {
                if (rawGroup) { rawGroup.classList.remove("hidden"); rawGroup.style.display = ""; }
            } else {
                if (rawGroup) { rawGroup.classList.add("hidden"); rawGroup.style.display = "none"; }
                if (rawPath) rawPath.value = "";
            }
        });
    });
    checkImportFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
