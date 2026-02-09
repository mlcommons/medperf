function onBenchmarkRegisterSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Benchmark Successfully Registered", seconds: 3, url: "/benchmarks/ui/display/" + response.benchmark_id });
    } else {
        showErrorModal("Benchmark Registration Failed", response);
    }
}

function registerBenchmark(registerButton) {
    addSpinner(registerButton);
    var form = document.getElementById("benchmark-register-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#benchmark-register-form input, #benchmark-register-form textarea, #benchmark-register-form select, #benchmark-register-form button");
    ajaxRequest("/benchmarks/register", "POST", formData, onBenchmarkRegisterSuccess, "Error registering benchmark:");
    showPanel("Registering Benchmark...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function checkBenchmarkFormValidity() {
    var nameEl = document.getElementById("name");
    var descEl = document.getElementById("description");
    var urlEl = document.getElementById("reference-dataset-tarball-url");
    var dataPrepEl = document.getElementById("data-preparation-container");
    var refModelEl = document.getElementById("reference-model-container");
    var evalEl = document.getElementById("evaluator-container");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var descriptionValue = descEl ? descEl.value.trim() : "";
    var referenceDatasetTarballUrlValue = urlEl ? urlEl.value.trim() : "";
    var dataPreparationContainerValue = dataPrepEl && dataPrepEl.value ? Number(dataPrepEl.value) : 0;
    var referenceModelContainerValue = refModelEl && refModelEl.value ? Number(refModelEl.value) : 0;
    var evaluatorContainerValue = evalEl && evalEl.value ? Number(evalEl.value) : 0;
    var isValid = nameValue.length > 0 && descriptionValue.length > 0 && referenceDatasetTarballUrlValue.length > 0 && dataPreparationContainerValue > 0 && referenceModelContainerValue > 0 && evaluatorContainerValue > 0;
    var btn = document.getElementById("register-benchmark-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var btn = document.getElementById("register-benchmark-btn");
    if (btn) btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, registerBenchmark, "register this benchmark?"); });
    var form = document.getElementById("benchmark-register-form");
    if (form) {
        form.querySelectorAll("input, textarea, select").forEach(function (el) {
            el.addEventListener("keyup", checkBenchmarkFormValidity);
            el.addEventListener("change", checkBenchmarkFormValidity);
        });
    }
    checkBenchmarkFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
