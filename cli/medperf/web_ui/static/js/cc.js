/*
 * Confidential computing (CC) configuration of a model or dataset
 * (see macros/cc_asset_macro.html): enabling CC, its GCP settings and syncing
 * the CC policy. The Apply button is enabled when the settings changed and,
 * if CC is enabled, all of its fields are filled (getFormProblems, see form_validation.js).
 */

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

/** Handle the response of saving the CC configuration. */
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

/** Handle the response of syncing the CC policy. */
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

/** Whether the CC configuration differs from the saved one. */
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

/**
 * Return the problems preventing the configuration from being applied:
 * when CC is enabled, all of its fields are required.
 */
function getFormProblems() {
    var problems = [];
    var configureEl = document.getElementById("configure-cc");
    if (!configureEl || !configureEl.checked) {
        return problems; // If CC is not configured, no need to validate fields
    }
    for (var i = 0; i < CC_ASSET_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_ASSET_FIELD_IDS[i]);
        var label = document.querySelector("label[for='" + CC_ASSET_FIELD_IDS[i] + "']");
        requireValue(problems, el, "Fill in " + (label ? label.textContent.trim() : "all the fields"));
    }
    return problems;
}

/** Enable the Apply button when the configuration can be saved. */
function checkCanApplyChanges() {
    var preferences = window.ccPreferences || {};

    var canApplyWithoutChanges = !preferences.initialized && preferences.configured;
    var hasChanges = checkForCCAssetChanges();

    var applyBtn = document.getElementById("apply-cc-asset-btn");
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

/** Bind the CC configuration and policy forms. */
function initCCAsset() {
    var form = document.getElementById("edit-cc-asset-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        var configureEl = document.getElementById("configure-cc");
        var fieldsContainer = document.getElementById("edit-cc-asset-fields");
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
