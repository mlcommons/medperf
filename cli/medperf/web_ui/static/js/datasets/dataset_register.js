/*
 * Dataset registration page.
 */

var REDIRECT_BASE = "/datasets/ui/display/";

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkDatasetFormValidity() {
    var benchmarkEl = document.getElementById("benchmark");
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var locationEl = document.getElementById("location");
    var dataPathEl = document.getElementById("data-path");
    var labelsPathEl = document.getElementById("labels-path");
    var problems = [];
    if (window.ui_mode === window.evaluation_mode && benchmarkEl && !benchmarkEl.value) {
        problems.push({ field: benchmarkEl, message: "Select a benchmark" });
    }
    requireValue(problems, nameEl, "Enter the dataset name");
    requireValue(problems, descEl, "Enter a description");
    requireValue(problems, locationEl, "Enter the dataset location");
    requireValue(problems, dataPathEl, "Enter the data path");
    requireValue(problems, labelsPathEl, "Enter the labels path");

    var btn = document.getElementById("register-dataset-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the registration form and its path pickers. */
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
