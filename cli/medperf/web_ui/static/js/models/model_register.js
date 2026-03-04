function onModelRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal({
            title: "Model Registered Successfully",
            seconds: 3,
            url: "/models/ui/display/" + response.model_id
        });
    }
    else{
        showErrorModal("Failed to Register Model", response);
    }
}

async function registerModel(registerButton){
    addSpinner(registerButton);

    const formData = new FormData($("#model-register-form")[0]);

    disableElements("#model-register-form input, #model-register-form button, #model-register-form select");

    ajaxRequest(
        "/models/register",
        "POST",
        formData,
        onModelRegisterSuccess,
        "Error registering model:"
    );

    showPanel(`Registering Model...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkModelFormValidity() {
    const name = $("#name").val().trim();
    const modelType = $("input[name='model_type']:checked").val();

    let isValid = Boolean(name);

    if(modelType === "container") {
        const containerPath = $("#container-file").val().trim();
        const isEncrypted = $("input[name='model_encrypted']:checked").val();
        const decryptionPath = $("#decryption-file").val().trim();
        isValid = isValid && Boolean(
            containerPath.length > 0 &&
            (isEncrypted === "true" ? decryptionPath.length > 0 : isEncrypted === "false")
        );
    } else if(modelType === "asset") {
        const assetSource = $("input[name='asset_source']:checked").val();
        if(assetSource === "path") {
            isValid = isValid && Boolean($("#asset-path").val().trim().length > 0);
        } else {
            isValid = isValid && Boolean($("#asset-url").val().trim().length > 0);
        }
    } else {
        isValid = false;
    }

    $("#register-model-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-model-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerModel, "register this model?");
    });

    // Toggle container vs asset fields
    $("input[name='model_type']").on("change", () => {
        const modelType = $("input[name='model_type']:checked").val();
        if(modelType === "container") {
            $("#container-fields").show();
            $("#asset-fields").hide();
        } else {
            $("#container-fields").hide();
            $("#asset-fields").show();
        }
        checkModelFormValidity();
    });

    // Toggle asset source (path vs url)
    $("input[name='asset_source']").on("change", () => {
        const assetSource = $("input[name='asset_source']:checked").val();
        if(assetSource === "path") {
            $("#asset-path-container").show();
            $("#asset-url-container").hide();
            $("#asset-url").val("");
        } else {
            $("#asset-path-container").hide();
            $("#asset-url-container").show();
            $("#asset-path").val("");
        }
        checkModelFormValidity();
    });

    // Toggle encryption fields
    $("input[name='model_encrypted']").on("change", () => {
        if($("#with-encryption").is(":checked")){
            $("#decryption-file-container").show();
        }
        else{
            $("#decryption-file-container").hide();
            $("#decryption-file").val("");
        }
        checkModelFormValidity();
    });

    // Browse buttons
    $("#browse-container-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("container-file");
    });
    $("#browse-parameters-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("parameters-file");
    });
    $("#browse-decryption-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("decryption-file");
    });
    $("#browse-asset-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("asset-path");
    });

    // Form validity checks on input change
    $("#model-register-form input").on("keyup change", checkModelFormValidity);

    // Initialize visibility
    $("input[name='model_type']:checked").trigger("change");
});
