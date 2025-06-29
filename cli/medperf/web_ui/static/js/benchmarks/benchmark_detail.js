
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

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function createEmailChip(email, input_element) {
    const $chip = $("<div class='email-chip'></div>").text(email);
    const $remove = $("<span class='remove-btn'>&times;</span>");

    $remove.on("click", function () {
        $chip.remove();
    });

    $chip.append($remove);
    input_element.before($chip);
}

function parseEmails(element){
    const jsonList = JSON.parse(element.attr("data-allowed-list"));
    const input_element = element.find("input");
    if(jsonList.length){
        jsonList.forEach(email => {
            createEmailChip(email, input_element);
        });
    }
}

function getEmailsList(element){
    const emailsArr = [];
    element.find(".email-chip").each(function() {
        const span = $(this).find("span");
        span.remove();
        emailsArr.push($(this).text().trim());
        $(this).append(span);
    });
    return emailsArr;
}

function showErrorToast(message){
    showToast("Validation Error", message, "bg-danger text-light");
}

function checkUpdateAssociationsPolicyForm(){
    let isDatasetValid = false, isModelValid = false;

    const datasetApproveMode = $("#dataset-auto-approve-mode").val();
    const modelApproveMode = $("#model-auto-approve-mode").val();

    isDatasetValid = (datasetApproveMode === "NEVER" || datasetApproveMode === "ALWAYS");
    isModelValid = (modelApproveMode === "NEVER" || modelApproveMode === "ALWAYS")

    if(!isDatasetValid){
        const datasetAllowListArr = getEmailsList($("#dataset-allow-list-emails"));
        if(datasetAllowListArr.length)
            isDatasetValid = true;
        else{
            showErrorToast("Make sure that the dataset allow list is not empty");
        }
    }
    if(!isModelValid){
        const modelAllowListArr = getEmailsList($("#model-allow-list-emails"));
        if(modelAllowListArr.length)
            isModelValid = true
        else{
            showErrorToast("Make sure that the model allow list is not empty");
        }
    }
    return isDatasetValid && isModelValid;
}

function onUpdateAssociationsPolicySuccess(response){
    if(response.status === "success"){
        showReloadModal("Benchmark Associations Policy Successfully Updated");
        timer(3);
    }
    else{
        showErrorModal("Failed to Update Benchmark Associations Policy", response);
    }
}

async function updateAssociationsPolicy(saveBtn){
    addSpinner(saveBtn);

    disableElements(".card button, .card input, .card select");
    
    const formData = new FormData();

    const datasetApproveMode = $("#dataset-auto-approve-mode").val();
    const modelApproveMode = $("#model-auto-approve-mode").val();

    if(datasetApproveMode === "ALLOWLIST"){
        const datasetAllowListArr = getEmailsList($("#dataset-allow-list-emails"));
        formData.append("dataset_emails", datasetAllowListArr.join(" "));
    } 
    if(modelApproveMode === "ALLOWLIST"){
        const modelAllowListArr = getEmailsList($("#model-allow-list-emails"));
        formData.append("model_emails", modelAllowListArr.join(" "));
    }

    formData.append("benchmark_id", saveBtn.getAttribute("data-benchmark-id"));
    formData.append("dataset_mode", datasetApproveMode);
    formData.append("model_mode", modelApproveMode);
    
    ajaxRequest(
        `/benchmarks/update_associations_policy`,
        "POST",
        formData,
        onUpdateAssociationsPolicySuccess,
        "Failed to update associations policy"
    );

    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

$(document).ready(() => {
    $("[id^='show-']").on("click", (e) => {
        showResult(e.currentTarget);
    });
    
    $("#datasets-associations-title").on("click", () => {
        $("#datasets-associations").slideToggle(); // smooth animation
    });
    
    $("#models-associations-title").on("click", () => {
        $("#models-associations").slideToggle(); // smooth animation
    });
    
    $("#benchmark-results-title").on("click", () => {
        $("#benchmark-results").slideToggle(); // smooth animation
    });
    
    $("#benchmark-results-title").on("click", () => {
        $("#benchmark-results").slideToggle(); // smooth animation
    });
    
    $("#dataset-auto-approve-mode").on("change", (e) => {
        if(e.currentTarget.value === "ALLOWLIST"){
            $("#dataset-allow-list-container").removeClass("d-none");
        }
        else{
            $("#dataset-allow-list-container").addClass("d-none");
        }
    });
    
    $("#model-auto-approve-mode").on("change", (e) => {
        if(e.currentTarget.value === "ALLOWLIST"){
            $("#model-allow-list-container").removeClass("d-none");
        }
        else{
            $("#model-allow-list-container").addClass("d-none");
        }
    });

    parseEmails($("#model-allow-list-emails"));
    parseEmails($("#dataset-allow-list-emails"));
    
    $(".email-input").on("keydown", function (e) {
        if (e.key === "Enter" || e.key === " " || e.key === ",") {
            e.preventDefault();
            let email = $(this).val().trim().replace(/,$/, "");
            if (email && isValidEmail(email)) {
                createEmailChip(email, $(this));
                $(this).val("");
            }
        }
    });

    $(".email-input").on("paste", function (e) {
        e.preventDefault();
        let clipboardData = (e.originalEvent || e).clipboardData.getData("text");
        let rawEmails = clipboardData.split(/[\s,]+/);
        rawEmails.forEach(email => {
            email = email.trim();
            if (email && isValidEmail(email)) {
                createEmailChip(email, $(this));
            }
        });
        $(this).val("");
    });

    $("#save-policy-btn").on("click", (e) => {
        if(checkUpdateAssociationsPolicyForm()){
            showConfirmModal(e.currentTarget, updateAssociationsPolicy, "want to update benchmark associations policy?");
        }
    });

    $("#dataset-auto-approve-mode").trigger("change");
    $("#model-auto-approve-mode").trigger("change");
});