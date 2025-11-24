
function checkAccessForm(){
    const allowListArr = getEmailsList($("#allowed-email-list"));

    if(!$("#benchmark").val()){
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    
    if(!allowListArr.length){
        showErrorToast("Make sure that the email allow list is not empty");
        return false;
    }

    return true;
}

function checkAutoAccessForm(){
    const allowListArr = getEmailsList($("#allowed-email-list-auto"));

    if(!$("#benchmark-auto").val()){
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    
    const interval = $("#interval-auto").val()

    if(!interval || interval < 5 || interval > 60){
        showErrorToast("Make sure that the time interval is between 5 and 60 (inclusive)");
        return false;
    }

    if(!allowListArr.length){
        showErrorToast("Make sure that the email allow list is not empty");
        return false;
    }

    return true;
}

function onGrantAccessSuccess(response){
    if(response.status === "success"){
        showReloadModal("Successfully Granted Access to the Selected Users");
        timer(3);
    }
    else{
        showErrorModal("Failed to Grant Access", response);
    }
}

async function grantAccess(grantBtn){
    addSpinner(grantBtn);

    disableElements(".card button, .card input, .card select");
    
    const allowListArr = getEmailsList($("#allowed-email-list"));
    const formData = new FormData();

    formData.append("benchmark_id", $("#benchmark").val());
    formData.append("model_id", grantBtn.getAttribute("data-model-id"))
    formData.append("emails", allowListArr.join(" "));
    
    ajaxRequest(
        `/containers/grant_access`,
        "POST",
        formData,
        onGrantAccessSuccess,
        "Failed to grant access"
    );

    showPanel(`Granting Access...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function startAutoGrant(startBtn){
    disableElements(".card button, .card input, .card select");
    
    const allowListArr = getEmailsList($("#allowed-email-list-auto"));
    const formData = new FormData();

    formData.append("benchmark_id", $("#benchmark-auto").val());
    formData.append("model_id", startBtn.getAttribute("data-model-id"))
    formData.append("interval", $("#interval-auto").val());
    formData.append("emails", allowListArr.join(" "));
    
    ajaxRequest(
        `/containers/start_auto_access`,
        "POST",
        formData,
        (response) => {
            if(response.status === "success"){
                showReloadModal("Successfully Started Auto Grant Access");
                timer(2);
            }
            else{
                showErrorModal("Failed to Start Auto Grant Access", response);
            }
        },
        "Failed to start auto grant access"
    );
}

async function stopAutoGrant(stopBtn){
    disableElements(".card button, .card input, .card select");
    
    const formData = new FormData();

    formData.append("model_id", stopBtn.getAttribute("data-model-id"))

    ajaxRequest(
        `/containers/stop_auto_access`,
        "POST",
        formData,
        (response) => {
            if(response.status === "success"){
                showReloadModal("Successfully Stopped Auto Grant Access");
                timer(2);
            }
            else{
                showErrorModal("Failed to Stop Auto Grant Access", response);
            }
        },
        "Failed to stop auto grant access"
    );
}

function onrevokeUserAccessSuccess(response){
    if(response.status === "success"){
        showReloadModal("Successfully Revoked User Access");
        timer(3);
    }
    else{
        showErrorModal("Failed to Revoke User Access", response);
    }
}

async function revokeUserAccess(revokeAccessBtn){
    addSpinner(revokeAccessBtn);

    disableElements(".card button, .card input, .card select");
    
    const formData = new FormData();

    formData.append("model_id", revokeAccessBtn.getAttribute("data-model-id"))
    formData.append("key_id", revokeAccessBtn.getAttribute("data-key-id"))
    
    ajaxRequest(
        `/containers/revoke_user_access`,
        "POST",
        formData,
        onDeleteKeysSuccess,
        "Failed to revoke user access"
    );

    showPanel(`Revoking User Access...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function onDeleteKeysSuccess(response){
    if(response.status === "success"){
        showReloadModal("Successfully Deleted Keys");
        timer(3);
    }
    else{
        showErrorModal("Failed to Delete Keys", response);
    }
}

async function deleteKeys(deleteKeysBtn){
    addSpinner(deleteKeysBtn);

    disableElements(".card button, .card input, .card select");
    
    const formData = new FormData();

    formData.append("model_id", deleteKeysBtn.getAttribute("data-model-id"))
    
    ajaxRequest(
        `/containers/delete_keys`,
        "POST",
        formData,
        onDeleteKeysSuccess,
        "Failed to delete keys"
    );

    showPanel(`Deleting Keys...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function showErrorToast(message){
    showToast("Validation Error", message, "bg-danger text-light");
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
    if (!$(element).length || !$(element))
        return;
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


$(document).ready(() => {
    parseEmails($("#allowed-email-list"));
    
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

    $("#grant-access-btn").on("click", (e) => {
        if(checkAccessForm()){
            showConfirmModal(e.currentTarget, grantAccess, "want to grant access to the emails added?");
        }
    });

    $("#start-auto-access-btn").on("click", (e) => {
        if(checkAutoAccessForm()){
            showConfirmModal(e.currentTarget, startAutoGrant, "want to start automatic grant access for the selected benchmark?");
        }
    });

    $("#stop-auto-access-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, stopAutoGrant, "want to stop automatic grant access?");
    });

    $(".revoke-access-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, revokeUserAccess, "want to revoke access for the selected user?");

    });

    $("#delete-keys-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, deleteKeys, "want to delete all keys?");

    });
});