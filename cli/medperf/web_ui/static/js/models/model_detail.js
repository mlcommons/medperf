function onModelAssociationRequestSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal({
            title: "Association Requested Successfully",
            seconds: 3,
        });
    }
    else{
        showErrorModal("Association Request Failed", response);
    }
}

async function requestModelAssociation(requestAssociationButton){
    $("#dropdown-div").removeClass("show");
    addSpinner($("#associate-dropdown-btn")[0]);

    const modelId = requestAssociationButton.getAttribute("data-model-id");
    const benchmarkId = requestAssociationButton.getAttribute("data-benchmark-id");

    const formData = new FormData();
    formData.append("model_id", modelId);
    formData.append("benchmark_id", benchmarkId);

    disableElements(".card button");

    ajaxRequest(
        "/models/associate",
        "POST",
        formData,
        onModelAssociationRequestSuccess,
        "Error requesting model association:"
    );

    showPanel(`Requesting Model Association...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}


$(document).ready(() => {
    $(".request-association-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, requestModelAssociation, "request model association?");
    });
});
