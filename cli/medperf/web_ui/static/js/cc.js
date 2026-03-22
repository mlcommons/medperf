/* CC asset (model/dataset) configuration: uses our form design with submitActionForm and data-success-handler. */

var CC_ASSET_FIELD_IDS = [
    "cc-project_id",
    "cc-project_number",
    "cc-bucket",
    "cc-keyring_name",
    "cc-key_name",
    "cc-key_location",
    "cc-wip",
    "cc-wip_provider",
];

function onCCEditRequestSuccess(response) {
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

function onCCPolicyRequestSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({
            title: "CC Policy Synced Successfully",
            seconds: 3,
        });
    } else {
        showErrorModal("Failed to Sync CC Policy", response);
    }
}

function checkForCCAssetChanges() {
    var preferences = window.ccPreferences || {};
    var defaultConfigureChecked = preferences.configured;
    var defaults = preferences.defaults || {};
    var configureEl = document.getElementById("configure-cc");
    var configureChecked = configureEl ? configureEl.checked : false;
    if (configureChecked !== defaultConfigureChecked) {
        return true;
    }
    if (!configureChecked) {
        // If checkbox was turned on, some input were written, then turned off, no changes.
        return false;
    }
    for (var i = 0; i < CC_ASSET_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_ASSET_FIELD_IDS[i]);
        if (el) {
            var currentValue = el.value || "";
            var defaultKey = CC_ASSET_FIELD_IDS[i].replace(/^cc-/, "");
            var defaultValue = (defaults[defaultKey] !== undefined) ? defaults[defaultKey] : "";
            if (currentValue !== defaultValue) return true;
        }
    }
    return false;
}

function checkFormValidity() {
    var configureEl = document.getElementById("configure-cc");
    var configureChecked = configureEl ? configureEl.checked : false;
    if (!configureChecked) {
        return true; // If CC is not configured, no need to validate fields
    }
    for (var i = 0; i < CC_ASSET_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_ASSET_FIELD_IDS[i]);
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
    var preferences = window.ccPreferences || {};

    var canApplyWithoutChanges = !preferences.initialized && preferences.configured;
    var hasChanges = checkForCCAssetChanges();

    var applyBtn = document.getElementById("apply-cc-asset-btn");
    if (applyBtn) {
        if (!hasChanges) {
            applyBtn.disabled = !canApplyWithoutChanges;
        }
        else {
            applyBtn.disabled = !checkFormValidity();
        }
    }
}

function initCCAsset() {
    var form = document.getElementById("edit-cc-asset-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        var configureEl = document.getElementById("configure-cc");
        var fieldsContainer = document.getElementById("edit-cc-asset-fields");
        if (configureEl && fieldsContainer) {
            function toggleFields() {
                fieldsContainer.style.display = configureEl.checked ? "" : "none";
                if (!configureEl.checked) fieldsContainer.classList.add("hidden");
                else fieldsContainer.classList.remove("hidden");
            }
            configureEl.addEventListener("change", toggleFields);
            toggleFields();
        }
        var inputs = form.querySelectorAll("input[type='text'], input[id='configure-cc']");
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].addEventListener("keyup", checkCanApplyChanges);
            inputs[i].addEventListener("change", checkCanApplyChanges);
        }
        checkCanApplyChanges();
    }
    var syncForm = document.getElementById("sync-cc-policy-form");
    if (syncForm) syncForm.addEventListener("submit", submitActionForm);

    var configureEl = document.getElementById("configure-cc");
    if (configureEl) configureEl.addEventListener("change", function() {
        var syncBtn = document.getElementById("sync-cc-policy-btn");
        if (syncBtn) {
            syncBtn.style.display = configureEl.checked ? "" : "none";
        }
    });

}

if (typeof window !== "undefined") {
    window.onCCEditRequestSuccess = onCCEditRequestSuccess;
    window.onCCPolicyRequestSuccess = onCCPolicyRequestSuccess;
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCCAsset);
else initCCAsset();
