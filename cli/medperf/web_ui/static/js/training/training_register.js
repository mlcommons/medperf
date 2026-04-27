var REDIRECT_BASE = "/training/ui/display/";

function onTrainingRegisterSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Training Experiment Successfully Registered", seconds: 3, url: "/training/ui/display/" + response.training_id });
    } else {
        showErrorModal("Training Experiment Registration Failed", response);
    }
}

function checkTrainingFormValidity() {
    var nameEl = document.getElementById("name");
    var dataPrepEl = document.getElementById("data-preparation-container");
    var flEl = document.getElementById("fl-container");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var dataPrepValue = dataPrepEl && dataPrepEl.value ? Number(dataPrepEl.value) : 0;
    var flValue = flEl && flEl.value ? Number(flEl.value) : 0;
    var isValid = nameValue.length > 0 && dataPrepValue > 0 && flValue > 0;
    var btn = document.getElementById("register-training-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var form = document.getElementById("register-training-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input, textarea, select").forEach(function (el) {
            el.addEventListener("keyup", checkTrainingFormValidity);
            el.addEventListener("change", checkTrainingFormValidity);
        });
    }
    checkTrainingFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
