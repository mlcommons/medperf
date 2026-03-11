const fields = [
    "cc-project_id",
    "cc-project_number",
    "cc-bucket",
    "cc-keyring_name",
    "cc-key_name",
    "cc-wip",
    "require-cc"
];

function checkForCCEditChanges() {
    // const hasChanges = fields.some(field => {
    //     return $(`#${field}`).val() !== window.defaultCCConfig[field];
    // });
    // TODO
    hasChanges = true;
    $('#apply-cc-asset-btn').prop('disabled', !hasChanges);
}

function editCCConfig(editCCConfigBtn) {
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
    const checkbox = $("#require-cc");
    checkbox.on("change", () => {
        $("#edit-cc-asset-fields").toggle(checkbox.is(":checked"));
    });
    $("#edit-cc-asset-fields").toggle(checkbox.is(":checked"));

    fields.forEach(field => $(`#${field}`).on('input', checkForCCEditChanges));
    checkForCCEditChanges();
    
    $("#apply-cc-asset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editCCConfig, "edit CC configuration?");
    });

});
