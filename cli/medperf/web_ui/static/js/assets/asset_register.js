function onAssetRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal({
            title: "Asset Registered Successfully",
            seconds: 3,
            url: "/assets/ui/display/"+response.asset_id
        });
    }
    else{
        showErrorModal("Failed to Register Asset", response);
    }
}

async function registerAsset(registerButton){
    addSpinner(registerButton);

    const formData = new FormData($("#asset-register-form")[0]);

    disableElements("#asset-register-form input, #asset-register-form button");

    ajaxRequest(
        "/assets/register",
        "POST",
        formData,
        onAssetRegisterSuccess,
        "Error registering asset:"
    )

    showPanel(`Registering Asset...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkAssetFormValidity() {
    const assetURL = $("#asset-url").val().trim();
    const isRemote = $("input[name='asset_is_remote']:checked").val();
    const assetPath = $("#asset-path").val().trim();

    const isValid = Boolean(
        $("#name").val().trim() &&
        (isRemote === "true" ? assetURL.length > 0 : isRemote === "false" && assetPath.length > 0)
    );
    $("#register-asset-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-asset-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerAsset, "register this asset?");
    });

    $("#asset-register-form input").on("keyup change", checkAssetFormValidity);
    
    $("#browse-asset-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("asset-path");
    });
    $("input[name='asset_is_remote']").on("change", () => {
        if($("#local").is(":checked")){
            $("#asset-path-container").show();
            $("#asset-url-container").hide();
            $("#asset-url").val("");
        }
        else{
            $("#asset-url-container").show();
            $("#asset-path-container").hide();
            $("#asset-path").val("");
        }
    });
});
