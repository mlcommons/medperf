/*
 * Training experiment registration page.
 */

var REDIRECT_BASE = "/training/ui/display/";

/** Handle the registration response. */
function onTrainingRegisterSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Training Experiment Successfully Registered", seconds: 3, url: "/training/ui/display/" + response.training_id });
    } else {
        showErrorModal("Training Experiment Registration Failed", response);
    }
}

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkTrainingFormValidity() {
    var nameEl = document.getElementById("name");
    var dataPrepEl = document.getElementById("data-preparation-container");
    var flEl = document.getElementById("fl-container");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var dataPrepValue = dataPrepEl && dataPrepEl.value ? Number(dataPrepEl.value) : 0;
    var flValue = flEl && flEl.value ? Number(flEl.value) : 0;

    var problems = [];
    if (!nameValue) problems.push({ field: nameEl, message: "Enter the training experiment name" });
    if (!(dataPrepValue > 0)) problems.push({ field: dataPrepEl, message: "Select the data preparation container" });
    if (!(flValue > 0)) problems.push({ field: flEl, message: "Select the FL container" });

    var btn = document.getElementById("register-training-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the registration form. */
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
