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

    showPanel(`Registering Model...`);
    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkContainerFormValidity() {
    const containerPath = $("#container-file").val().trim();

    const isValid = Boolean(
        $("#name").val().trim() &&
        containerPath.length > 0 &&
        containerPath.endsWith(".yaml")
    );
    $("#register-container-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-container-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerContainer, "register this container?");
    });

    $("#container-register-form input").on("keyup", checkContainerFormValidity);
    
    $("#browse-container-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("container-file");
    });

    $("#browse-parameters-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("parameters-file");
    });

    $("#browse-additional-btn").on("click", () => {
        browseWithFiles = true;
        browseFolderHandler("additional-file");
    });
});
