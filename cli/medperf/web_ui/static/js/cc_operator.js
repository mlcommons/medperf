/*
 * Confidential computing (CC) operator settings of the user, on the settings
 * page (see macros/cc_operator_macro.html). The Apply button is enabled when
 * the settings changed and, if CC is enabled, all of its fields are filled
 * (getFormProblems, see form_validation.js).
 */

var CC_OPERATOR_FIELD_IDS = [
    "operator-project_id",
    "operator-service_account_name",
    "operator-bucket",
    "operator-vm_zone",
    "operator-vm_name",
];
var CC_OPERATOR_DEFAULT_KEYS = ["project_id", "service_account_name", "bucket", "vm_zone", "vm_name"];

/** Handle the response of saving the CC operator settings. */
function onCCOperatorEditRequestSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({
            title: "CC Configuration Edited Successfully",
            seconds: 3,
        });
    } else {
        showErrorModal("Failed to Edit CC Configuration", response);
    }
}

/** Whether the CC operator settings differ from the saved ones. */
function checkForCCOperatorChanges() {
    var preferences = window.ccOperatorPreferences || window.ccPreferences || {};
    var defaultConfigureChecked = preferences.configured;
    var defaults = preferences.defaults || {};
    var configureEl = document.getElementById("configure-cc-operator");
    var configureChecked = configureEl ? configureEl.checked : false;
    if (configureChecked !== defaultConfigureChecked) {
        return true;
    }
    if (!configureChecked) {
        // If checkbox was turned on, some input were written, then turned off, no changes.
        return false;
    }
    for (var i = 0; i < CC_OPERATOR_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_OPERATOR_FIELD_IDS[i]);
        if (el) {
            var currentValue = el.value || "";
            var defaultKey = CC_OPERATOR_DEFAULT_KEYS[i];
            var defaultValue = (defaults[defaultKey] !== undefined) ? defaults[defaultKey] : "";
            if (currentValue !== defaultValue) return true;
        }
    }
    return false;
}

/**
 * Return the problems preventing the configuration from being applied:
 * when CC is enabled, all of its fields are required.
 */
function getFormProblems() {
    var problems = [];
    var configureEl = document.getElementById("configure-cc-operator");
    if (!configureEl || !configureEl.checked) {
        return problems; // If CC is not configured, no need to validate fields
    }
    for (var i = 0; i < CC_OPERATOR_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_OPERATOR_FIELD_IDS[i]);
        var label = document.querySelector("label[for='" + CC_OPERATOR_FIELD_IDS[i] + "']");
        requireValue(problems, el, "Fill in " + (label ? label.textContent.trim() : "all the fields"));
    }
    return problems;
}

/** Enable the Apply button when the settings can be saved. */
function checkCanApplyChanges() {
    var preferences = window.ccOperatorPreferences || window.ccPreferences || {};

    var canApplyWithoutChanges = !preferences.initialized && preferences.configured;
    var hasChanges = checkForCCOperatorChanges();

    var applyBtn = document.getElementById("apply-cc-operator-btn");
    if (applyBtn) {
        if (!hasChanges) {
            showFormProblems(applyBtn, []);
            applyBtn.disabled = !canApplyWithoutChanges;
        }
        else {
            applyBtn.disabled = !showFormProblems(applyBtn, getFormProblems());
        }
    }
}

/** Bind the CC operator settings form. */
function initCCOperator() {
    var form = document.getElementById("edit-cc-operator-form");
    if (!form) return;
    form.addEventListener("submit", submitActionForm);
    var configureEl = document.getElementById("configure-cc-operator");
    var fieldsContainer = document.getElementById("edit-cc-operator-fields");
    if (configureEl && fieldsContainer) {
        /** Show the CC fields only when CC is enabled. */
        function toggleFields() {
            fieldsContainer.style.display = configureEl.checked ? "" : "none";
            if (!configureEl.checked) fieldsContainer.classList.add("hidden");
            else fieldsContainer.classList.remove("hidden");
        }
        configureEl.addEventListener("change", toggleFields);
        toggleFields();
    }
    var inputs = form.querySelectorAll("input[type='text'], input[id='configure-cc-operator']");
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].addEventListener("keyup", checkCanApplyChanges);
        inputs[i].addEventListener("change", checkCanApplyChanges);
    }
    checkCanApplyChanges();
}

if (typeof window !== "undefined") {
    window.onCCOperatorEditRequestSuccess = onCCOperatorEditRequestSuccess;
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCCOperator);
else initCCOperator();
