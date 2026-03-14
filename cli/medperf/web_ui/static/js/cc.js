const fields = [
    "cc-project_id",
    "cc-project_number",
    "cc-bucket",
    "cc-keyring_name",
    "cc-key_name",
    "cc-key_location",
    "cc-wip",
    "cc-wip_provider",
];

function onCCEditRequestSuccess(response){
    markAllStagesAsComplete();
    if (response.status === "success"){
        showReloadModal({
            title: "CC Configuration Edited Successfully",
            seconds: 3
        });
    }
    else {
        showErrorModal("Failed to Edit CC Configuration", response);
    }
}

function onCCPolicyRequestSuccess(response){
    if (response.status === "success"){
        showReloadModal({
            title: "CC Policy Synced Successfully",
            seconds: 3
        });
    }
    else {
        showErrorModal("Failed to Sync CC Policy", response);
    }
}


function checkForCCEditChanges() {
    const preferences = window.ccPreferences || {};
    const configured = preferences.can_apply;
    const defaults = preferences.defaults || {};
    const requireCCChanged = ($("#require-cc").is(":checked") !== configured)
    var hasChanges = fields.some(field => {
        let currentValue = $(`#${field}`).val();
        let defaultValue = defaults[field] || "";
        return currentValue !== defaultValue;
    });
    hasChanges = hasChanges || requireCCChanged;
    $('#apply-cc-asset-btn').prop('disabled', !hasChanges);
}

function SyncCCPolicy(syncCCPolicyBtn) {
    const entityId = syncCCPolicyBtn.getAttribute("data-entity-id");
    const entityType = syncCCPolicyBtn.getAttribute("data-entity-type");
    const url = `/${entityType}s/sync_cc_policy`;
    const formData = new FormData();
    formData.append("entity_id", entityId);

    disableElements(syncCCPolicyBtn);
    disableElements(".card button");
    ajaxRequest(
        url,
        "POST",
        formData,
        onCCPolicyRequestSuccess,
        "Error syncing CC policy:"
    );
}

async function editCCConfig(editCCConfigBtn) {
    const formData = new FormData($("#edit-cc-asset-form")[0]);
    const entityId = editCCConfigBtn.getAttribute("data-entity-id");
    const entityType = editCCConfigBtn.getAttribute("data-entity-type");
    formData.append("entity_id", entityId);
    const url = `/${entityType}s/edit_cc_config`;

    disableElements("#edit-cc-asset-form input, #edit-cc-asset-form button");
    disableElements(".card button");

    ajaxRequest(
        url,
        "POST",
        formData,
        onCCEditRequestSuccess,
        "Error editing CC Configuration:"
    );
    showPanel(`Updating Model CC Configuration...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}


$(document).ready(() => {    
    const checkbox = $("#require-cc");
    checkbox.on("change", () => {
        $("#edit-cc-asset-fields").toggle(checkbox.is(":checked"));
    });
    $("#edit-cc-asset-fields").toggle(checkbox.is(":checked"));

    fields + ["require-cc"].forEach(field => $(`#${field}`).on('keyup, change', checkForCCEditChanges));
    checkForCCEditChanges();
    
    $("#apply-cc-asset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editCCConfig, "edit CC configuration?");
    });

    $("#sync-cc-policy-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, SyncCCPolicy, "sync CC policy?");
    });
});
