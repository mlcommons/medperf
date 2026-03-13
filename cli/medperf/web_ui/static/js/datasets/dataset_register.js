REDIRECT_BASE = "/datasets/ui/display/";

function checkDatasetFormValidity() {
    var benchmarkEl = document.getElementById("benchmark");
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var locationEl = document.getElementById("location");
    var dataPathEl = document.getElementById("data-path");
    var labelsPathEl = document.getElementById("labels-path");
    var isValid = !!(nameEl && nameEl.value.trim()) && !!(descEl && descEl.value.trim()) && !!(locationEl && locationEl.value.trim()) && !!(dataPathEl && dataPathEl.value.trim()) && !!(labelsPathEl && labelsPathEl.value.trim());
    if(window.ui_mode === window.evaluation_mode){
        isValid = isValid  && !!(benchmarkEl && benchmarkEl.value);
    }
    var btn = document.getElementById("register-dataset-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var form = document.getElementById("register-dataset-form");
    if (form){
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input, select, textarea").forEach(function (el) {
            el.addEventListener("change", checkDatasetFormValidity);
            el.addEventListener("keyup", checkDatasetFormValidity);
        });
    }
    var browseData = document.getElementById("browse-data-btn");
    var browseLabels = document.getElementById("browse-labels-btn");
    if (browseData) browseData.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("data-path"); });
    if (browseLabels) browseLabels.addEventListener("click", function () { browseWithFiles = false; browseFolderHandler("labels-path"); });
    checkDatasetFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
