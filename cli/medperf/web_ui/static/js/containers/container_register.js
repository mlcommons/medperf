function onContainerRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Model Registered Successfully");
        timer(3, "/containers/ui/display/"+response.container_id);
    }
    else{
        showErrorModal("Failed to Register Model", response);
    }
}

async function registerContainer(registerButton){
    addSpinner(registerButton);

    const formData = new FormData($("#container-register-form")[0]);

    disableElements("#container-register-form input, #container-register-form button");

    ajaxRequest(
        "/containers/register",
        "POST",
        formData,
        onContainerRegisterSuccess,
        "Error registering container:"
    )

    showPanel(`Registering Container...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkContainerFormValidity() {
    const containerPath = $("#container-file").val().trim();
    const isEncrypted = $("input[name='model_encrypted']:checked").val();
    const decryptionPath = $("#decryption-file").val().trim();

    const isValid = Boolean(
        $("#name").val().trim() &&
        containerPath.length > 0 &&
        (isEncrypted === "true" ? decryptionPath.length > 0 : isEncrypted === "false")
    );
    $("#register-container-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-container-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerContainer, "register this container?");
    });

    $("#container-register-form input").on("keyup change", checkContainerFormValidity);
    
    $("#browse-decryption-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("decryption-file");
    });
    $("input[name='model_encrypted']").on("change", () => {
        if($("#with-encryption").is(":checked")){
            $("#decryption-file-container").show();
        }
        else{
            $("#decryption-file-container").hide();
            $("#decryption-file").val("");
        }
    });
});
