const fields = [
    "operator-project_id",
    "operator-service_account_name",
    "operator-account",
    "operator-bucket",
    "operator-vm_zone",
    "operator-vm_network",
    "operator-boot_disk_size",
    "operator-gpus",
    "operator-machine_type",
    "require-cc-operator"
];

function checkForCCEditChanges() {
    // const hasChanges = fields.some(field => {
    //     return $(`#${field}`).val() !== window.defaultCCConfig[field];
    // });
    // TODO
    hasChanges = true;
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

    fields.forEach(field => $(`#${field}`).on('input', checkForCCEditChanges));
    checkForCCEditChanges();
    
    $("#apply-cc-operator-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editCCConfig, "edit CC configuration?");
    });

});
