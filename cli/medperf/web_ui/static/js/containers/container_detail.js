function onContainerAssociationRequestSuccess(response){
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

async function requestContainerAssociation(requestAssociationButton){
    $("#dropdown-div").removeClass("show");
    addSpinner($("#associate-dropdown-btn")[0]);

    const containerId = requestAssociationButton.getAttribute("data-container-id");
    const benchmarkId = requestAssociationButton.getAttribute("data-benchmark-id");

    const formData = new FormData();
    formData.append("container_id", containerId);
    formData.append("benchmark_id", benchmarkId);

    disableElements(".card button");

    ajaxRequest(
        "/containers/associate",
        "POST",
        formData,
        onContainerAssociationRequestSuccess,
        "Error requesting container association:"
    );

    showPanel(`Requesting Container Association...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}


$(document).ready(() => {
    $(".request-association-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, requestContainerAssociation, "request container association?");
    });
});