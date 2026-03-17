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
    var configured = preferences.can_apply;
    var defaults = preferences.defaults || {};
    var requireEl = document.getElementById("require-cc");
    var requireChecked = requireEl ? requireEl.checked : false;
    var requireCCChanged = (requireChecked !== configured);
    var hasChanges = requireCCChanged;
    for (var i = 0; i < CC_ASSET_FIELD_IDS.length; i++) {
        var el = document.getElementById(CC_ASSET_FIELD_IDS[i]);
        if (el) {
            var currentValue = el.value || "";
            var defaultKey = CC_ASSET_FIELD_IDS[i].replace(/^cc-/, "");
            var defaultValue = (defaults[defaultKey] !== undefined) ? defaults[defaultKey] : "";
            if (currentValue !== defaultValue) hasChanges = true;
        }
    }
    var applyBtn = document.getElementById("apply-cc-asset-btn");
    if (applyBtn) applyBtn.disabled = !hasChanges;
}

function initCCAsset() {
    var form = document.getElementById("edit-cc-asset-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        var requireEl = document.getElementById("require-cc");
        var fieldsContainer = document.getElementById("edit-cc-asset-fields");
        if (requireEl && fieldsContainer) {
            function toggleFields() {
                fieldsContainer.style.display = requireEl.checked ? "" : "none";
                if (!requireEl.checked) fieldsContainer.classList.add("hidden");
                else fieldsContainer.classList.remove("hidden");
            }
            requireEl.addEventListener("change", toggleFields);
            toggleFields();
        }
        var inputs = form.querySelectorAll("input[type='text'], input[id='require-cc']");
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].addEventListener("keyup", checkForCCAssetChanges);
            inputs[i].addEventListener("change", checkForCCAssetChanges);
        }
        checkForCCAssetChanges();
    }
    var syncForm = document.getElementById("sync-cc-policy-form");
    if (syncForm) syncForm.addEventListener("submit", submitActionForm);
}

if (typeof window !== "undefined") {
    window.onCCEditRequestSuccess = onCCEditRequestSuccess;
    window.onCCPolicyRequestSuccess = onCCPolicyRequestSuccess;
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCCAsset);
else initCCAsset();
