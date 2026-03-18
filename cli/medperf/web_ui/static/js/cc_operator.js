/* CC operator configuration (settings page): uses our form design with submitActionForm and data-success-handler. */

var CC_OPERATOR_FIELD_IDS = [
    "operator-project_id",
    "operator-service_account_name",
    "operator-bucket",
    "operator-vm_zone",
    "operator-vm_name",
];
var CC_OPERATOR_DEFAULT_KEYS = ["project_id", "service_account_name", "bucket", "vm_zone", "vm_name"];

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

function checkFormValidity() {
    var configureEl = document.getElementById("configure-cc-operator");
    var configureChecked = configureEl ? configureEl.checked : false;
    if (!configureChecked) {
        return true; // If CC is not configured, no need to validate fields
    }
    for (var i = 0; i < CC_OPERATOR_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_OPERATOR_FIELD_IDS[i]);
        if (el) {
            var currentValue = el.value.trim() || "";
            if (currentValue.length === 0) {
                return false; // If any configured field is empty, form is not valid
            }
        }
    }
    return true;
}

function checkCanApplyChanges() {
    var preferences = window.ccOperatorPreferences || window.ccPreferences || {};

    var canApplyWithoutChanges = !preferences.initialized && preferences.configured;
    var hasChanges = checkForCCOperatorChanges();

    var applyBtn = document.getElementById("apply-cc-operator-btn");
    if (applyBtn) {
        if (!hasChanges) {
            applyBtn.disabled = !canApplyWithoutChanges;
        }
        else {
            applyBtn.disabled = !checkFormValidity();
        }
    }
}

function initCCOperator() {
    var form = document.getElementById("edit-cc-operator-form");
    if (!form) return;
    form.addEventListener("submit", submitActionForm);
    var configureEl = document.getElementById("configure-cc-operator");
    var fieldsContainer = document.getElementById("edit-cc-operator-fields");
    if (configureEl && fieldsContainer) {
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
