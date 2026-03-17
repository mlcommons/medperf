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
    var configured = preferences.can_apply;
    var defaults = preferences.defaults || {};
    var requireEl = document.getElementById("require-cc-operator");
    var requireChecked = requireEl ? requireEl.checked : false;
    var requireCCChanged = (requireChecked !== configured);
    var hasChanges = requireCCChanged;
    for (var i = 0; i < CC_OPERATOR_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_OPERATOR_FIELD_IDS[i]);
        if (el) {
            var currentValue = el.value || "";
            var defaultKey = CC_OPERATOR_DEFAULT_KEYS[i];
            var defaultValue = (defaults[defaultKey] !== undefined) ? defaults[defaultKey] : "";
            if (currentValue !== defaultValue) hasChanges = true;
        }
    }
    var applyBtn = document.getElementById("apply-cc-operator-btn");
    if (applyBtn) applyBtn.disabled = !hasChanges;
}

function initCCOperator() {
    var form = document.getElementById("edit-cc-operator-form");
    if (!form) return;
    form.addEventListener("submit", submitActionForm);
    var requireEl = document.getElementById("require-cc-operator");
    var fieldsContainer = document.getElementById("edit-cc-operator-fields");
    if (requireEl && fieldsContainer) {
        function toggleFields() {
            fieldsContainer.style.display = requireEl.checked ? "" : "none";
            if (!requireEl.checked) fieldsContainer.classList.add("hidden");
            else fieldsContainer.classList.remove("hidden");
        }
        requireEl.addEventListener("change", toggleFields);
        toggleFields();
    }
    var inputs = form.querySelectorAll("input[type='text'], input[id='require-cc-operator']");
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].addEventListener("keyup", checkForCCOperatorChanges);
        inputs[i].addEventListener("change", checkForCCOperatorChanges);
    }
    checkForCCOperatorChanges();
}

if (typeof window !== "undefined") {
    window.onCCOperatorEditRequestSuccess = onCCOperatorEditRequestSuccess;
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCCOperator);
else initCCOperator();
