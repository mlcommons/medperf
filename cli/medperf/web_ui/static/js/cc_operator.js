const fields = [
    "operator-project_id",
    "operator-service_account_name",
    "operator-bucket",
    "operator-vm_zone",
    "operator-vm_network",
    "operator-boot_disk_size",
    "operator-gpus",
    "operator-machine_type",
];

function checkForCCEditChanges() {
    const preferences = window.ccPreferences || {};
    const configured = preferences.can_apply;
    const defaults = preferences.defaults || {};
    const requireCCChanged = ($("#require-cc-operator").is(":checked") !== configured)
    var hasChanges = fields.some(field => {
        let currentValue = $(`#${field}`).val();
        let defaultValue = defaults[field] || "";
        return currentValue !== defaultValue;
    });
    hasChanges = hasChanges || requireCCChanged;
    $('#apply-cc-operator-btn').prop('disabled', !hasChanges);    
}

function editCCConfig(editCCConfigBtn) {
    const formData = new FormData($("#edit-cc-operator-form")[0]);

    // TODO: properly disable elements
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button, #edit-config-form select");
    disableElements("#certificate-settings button");

    ajaxRequest(
        "/settings/edit_cc_operator",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal({
                    title: "CC Configuration Edited Successfully",
                    seconds: 3
                });
            }
            else {
                showErrorModal("Failed to Edit CC Configuration", response);
            }
        },
        "Error editing CC Configuration:"
    );
}


$(document).ready(() => {
    const checkbox = $("#require-cc-operator");
    checkbox.on("change", () => {
        $("#edit-cc-operator-fields").toggle(checkbox.is(":checked"));
    });
    $("#edit-cc-operator-fields").toggle(checkbox.is(":checked"));

    fields + ["require-cc-operator"].forEach(field => $(`#${field}`).on('keyup, change', checkForCCEditChanges));
    checkForCCEditChanges();
    
    $("#apply-cc-operator-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editCCConfig, "edit CC configuration?");
    });

});
