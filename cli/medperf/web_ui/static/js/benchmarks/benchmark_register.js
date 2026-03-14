var REDIRECT_BASE = "/benchmarks/ui/display/";

function checkBenchmarkFormValidity() {
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var urlEl = document.getElementById("reference-dataset-tarball-url");
    var dataPrepEl = document.getElementById("data-preparation-container");
    var refModelEl = document.getElementById("reference-model");
    var evalEl = document.getElementById("evaluator-container");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var descriptionValue = descEl ? descEl.value.trim() : "";
    var referenceDatasetTarballUrlValue = urlEl ? urlEl.value.trim() : "";
    var dataPreparationContainerValue = dataPrepEl && dataPrepEl.value ? Number(dataPrepEl.value) : 0;
    var referenceModelValue = refModelEl && refModelEl.value ? Number(refModelEl.value) : 0;
    var evaluatorContainerValue = evalEl && evalEl.value ? Number(evalEl.value) : 0;
    var isValid = nameValue.length > 0 && descriptionValue.length > 0 && referenceDatasetTarballUrlValue.length > 0 && dataPreparationContainerValue > 0 && referenceModelValue > 0 && evaluatorContainerValue > 0;
    var btn = document.getElementById("register-benchmark-btn");
    if (btn) btn.disabled = !isValid;
}

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
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
