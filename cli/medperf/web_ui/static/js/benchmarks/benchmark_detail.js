
function showConfirmationPrompt(approveRejectBtn){
    const entityType = approveRejectBtn.getAttribute("data-entity-type");
    const actionName = approveRejectBtn.getAttribute("data-action-name");
    const benchmarkId = approveRejectBtn.getAttribute("data-benchmark-id");
    const entityId = approveRejectBtn.getAttribute(`data-${entityType}-id`);

    $("#confirmation-btn").off("click").on("click", () => {
        approveRejectAssociation(actionName, benchmarkId, entityId, entityType, approveRejectBtn);
    });

    if(actionName==="approve"){
        $("#confirm-modal-title").text("Approval Confirmation");
        $("#confirm-text").html("Are you sure you want to approve this association?<br><span class='fs-5 text-danger fw-bold'>This action cannot be undone.</span>");
    }
    else{
        $("#confirm-modal-title").text("Rejection Confirmation");
        $("#confirm-text").html("Are you sure you want to reject this association?<br><span class='text-danger fw-bold'>This action cannot be undone.</span>");
    }

    const modal = new bootstrap.Modal('#confirm-modal', {
        keyboard: false,
        backdrop: "static"
    })
    modal.show();
}

function onApproveRejectAssociationSuccess(response, actionName){
    let title;
    if(response.status === "success"){
        if(actionName === "approve")
            title = "Association Approved Successfully";
        else
            title = "Association Rejected Successfully";
        showReloadModal(title);
        timer(3);
    }
    else{
        if(actionName === "approve")
            title = "Failed to Approve Association";
        else
            title = "Failed to Reject Association";
        showErrorModal(title, response)
    }
}
function onApproveRejectAssociationError(xhr, status, error, actionName){
    console.log("Error approving/rejecting associtation:", error);
    console.error("Error:", xhr.responseText);
}

function approveRejectAssociation(actionName, benchmarkId, entityId, entityType, approveRejectBtn){
    addSpinner(approveRejectBtn);
    disableElements(".card button");

    const formData = new FormData();
    formData.append("benchmark_id", benchmarkId);
    formData.append(`${entityType}_id`, entityId);

    $.ajax({
        url: `/benchmarks/${actionName}`,
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            onApproveRejectAssociationSuccess(response, actionName);
        },
        error: function(xhr, status, error){
            onApproveRejectAssociationError(xhr, status, error, actionName);
        }
    });

}

$(document).ready(() => {
    $("[id^='show-']").on("click", (e) => {
        showResult(e.currentTarget);
    });
});