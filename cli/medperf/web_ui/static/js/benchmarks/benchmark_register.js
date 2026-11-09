/*
 * Benchmark registration page.
 */

var REDIRECT_BASE = "/benchmarks/ui/display/";

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkBenchmarkFormValidity() {
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var urlEl = document.getElementById("reference-dataset-tarball-url");
    var dataPrepEl = document.getElementById("data-preparation-container");
    var refModelEl = document.getElementById("reference-model");
    var evalEl = document.getElementById("evaluator-container");
    var skipTestsEl = document.getElementById("skip-tests");
    var noSkipTestsEl = document.getElementById("noskip-tests");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var descriptionValue = descEl ? descEl.value.trim() : "";
    var referenceDatasetTarballUrlValue = urlEl ? urlEl.value.trim() : "";
    var dataPreparationContainerValue = dataPrepEl && dataPrepEl.value ? Number(dataPrepEl.value) : 0;
    var referenceModelValue = refModelEl && refModelEl.value ? Number(refModelEl.value) : 0;
    var evaluatorContainerValue = evalEl && evalEl.value ? Number(evalEl.value) : 0;
    var skipTestsValue = skipTestsEl && skipTestsEl.checked ? true : false;
    var noskipTestsValue = noSkipTestsEl && noSkipTestsEl.checked ? true: false;

    var problems = [];
    if (!nameValue) problems.push({ field: nameEl, message: "Enter the benchmark name" });
    if (!descriptionValue) problems.push({ field: descEl, message: "Enter a description" });
    if (!skipTestsValue && !noskipTestsValue) {
        problems.push({ field: null, message: "Choose whether to run the compatibility tests" });
    } else if (noskipTestsValue && !referenceDatasetTarballUrlValue) {
        problems.push({ field: urlEl, message: "Enter the reference dataset tarball URL (or skip the compatibility tests)" });
    }
    if (!(dataPreparationContainerValue > 0)) problems.push({ field: dataPrepEl, message: "Select the data preparation container" });
    if (!(referenceModelValue > 0)) problems.push({ field: refModelEl, message: "Select the reference model" });
    if (!(evaluatorContainerValue > 0)) problems.push({ field: evalEl, message: "Select the metrics container" });

    var btn = document.getElementById("register-benchmark-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/**
 * Bind the registration form, and show the demo dataset URL input only when
 * the compatibility tests are required.
 */
function init() {
    var form = document.getElementById("benchmark-register-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input, textarea, select").forEach(function (el) {
            el.addEventListener("keyup", checkBenchmarkFormValidity);
            el.addEventListener("change", checkBenchmarkFormValidity);
        });
    }
    checkBenchmarkFormValidity();
    document.querySelectorAll("input[name='skip_compatibility_tests']").forEach(function (el) {
        el.addEventListener("change", function () {
            var skipTestsEl = document.getElementById("skip-tests");
            var demoContainer = document.getElementById("demo-dataset-input-container");
            var urlInput = document.getElementById("reference-dataset-tarball-url");
            if (skipTestsEl && skipTestsEl.checked) {
                if (demoContainer) demoContainer.style.display = "none";
                if (urlInput) urlInput.value = "";
            } else {
                if (demoContainer) demoContainer.style.display = "block";
            }
        });
    });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
