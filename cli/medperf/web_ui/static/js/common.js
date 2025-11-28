function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const options = {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short"
    };
    if (date.getFullYear() !== now.getFullYear()) {
        options.year = "numeric";
    }
    return date.toLocaleDateString(undefined, options);
}

function applyDateFormatting() {
    const dateElements =  $("[data-date]");
    dateElements.each((_, element) => {
        const date = element.getAttribute("data-date");
        element.textContent = formatDate(date);
    });
}

// Floating alert notifications
function displayAlert(type, message) {
    const alertContainer = document.createElement("div");
    alertContainer.className = `alert alert-${type} alert-dismissible fade show floating-alert`;
    alertContainer.setAttribute("role", "alert");
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertContainer);
}

// Clear all alerts
function clearAlerts() {
    document.querySelectorAll(".floating-alert").forEach(alert => alert.remove());
}

function onRequestFailure(xhr, status, error, errorMessage){
    console.log(errorMessage, error);
    console.error("Error:", xhr.responseText);
}

function ajaxRequest(requestUrl, requestType, requestBody, successFunctionCallback, errorMessage){
    $.ajax({
        url: requestUrl,
        type: requestType,
        data: requestBody,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            successFunctionCallback(response);
            
        },
        error: function(xhr, status, error) {
            onRequestFailure(xhr, status, error, errorMessage);
        }
    });
}

function disableElements(selector){
    $(selector).prop("disabled", true);
}

function enableElements(selector){
    $(selector).prop("disabled", false);
}

function showReloadModal({ title, seconds, url=null }){
    const extra_fn = () => {
        timer({
            seconds: seconds,
            url: url
        });
    }

    showModal({
        title: title,
        body: '<p id="popup-text"></p>',
        extra_func: extra_fn
    });
}

function timer({seconds, url=null}){
    $("#popup-text").html(`The window will reload in <span id='timer'>${seconds}</span> ...`);
    const timerInterval = setInterval(function() {
        seconds--;
        $("#timer").text(seconds);

        if (seconds === 0) {
            clearInterval(timerInterval);
            if(url)
                window.location.href = url;
            else
                reloadPage();
        }
    }, 1000);
}

function markAllStagesAsComplete(){
    $("#stages-list > li").each((_, element) => {
        markStageAsComplete(element);
    });
}

function addSpinner(element){
    element.innerHTML += `
        <span class="spinner-border spinner-border-sm ms-2" role="status" aria-hidden="true"></span>
    `;
}

function showPanel(title){
    $("#panel-title").text(title);
    $("#panel").show();
}

function showErrorModal(errorTitle, response){
    const responseError = response.error;
    const responseStatus = response.status;
    let errorText = "";
    if (responseError){
        errorText += responseError.replace("\n", "<br>") + "<br>";
    }
    if (responseStatus){
        errorText += responseStatus.replace("\n", "<br>");
    }

    const modalBody = `
        <p id="error-text" class="fs-5 text-danger fw-bold">
            ${errorText}
        </p>

        <p class="text-end mt-3">
            <button type="button" class="btn" onclick="reloadPage();">
                Click here to reload
            </button>
        </p>
    `;
    const modalFooter = '<button type="button" class="btn btn-danger" data-bs-dismiss="modal">Hide</button>';

    showModal({
        title: errorTitle,
        body: modalBody,
        footer: modalFooter
    });
}

function showConfirmModal(clickedBtn, callback, message){
    const modalTitle = "Confirmation Prompt";
    const modalBody = `<p id="confirm-text" class="fs-5">Are you sure you want to ${message}</p>`;
    const modalFooter = `
    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">
        Cancel
    </button>

    <button id="confirmation-btn"
            type="button"
            class="btn btn-success"
            data-bs-dismiss="modal">
        Confirm
    </button>
    `;
    
    const extra_fn = () => {
        $("#confirmation-btn").off("click").on("click", () => {
            callback(clickedBtn);
        });
    };

    showModal({
        title: modalTitle,
        body: modalBody,
        footer: modalFooter,
        extra_func: extra_fn
    });
}

function getTaskId(){
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "/current_task",
            method: "get",
            success: function (response) {
                resolve(response.task_id);
            },
            error: function (xhr, status, error) {
                console.error("Failed to get task id:", error);
                reject(error);
            }
        });
    });
}

function respondToPrompt(value){
    $.ajax({
        url: "/events",
        type: "POST",
        data: { is_approved: value },
    });
    window.isPromptReceived = false;
    document.getElementById("prompt-text").innerHTML = "";
    document.getElementById("prompt-container").removeAttribute("style");
    streamEvents(logPanel, stagesList, currentStageElement);
}

function resumeRunningTask(buttonSelector, panelTitle, callback){
    if(buttonSelector){
        if (typeof buttonSelector === "object"){
            buttonSelector.forEach(selector => {
                addSpinner($(selector)[0]);
            });
        }
        else{
            addSpinner($(buttonSelector)[0]);
        }
    }
    
    if (panelTitle) {
        showPanel(panelTitle);
    }

    window.onPromptComplete = callback;
    streamEvents(logPanel, stagesList, currentStageElement, true);
}

function reloadPage(){
    window.location.reload(true);
}

function getEntities(switchElement){
    const entity_name = switchElement.getAttribute("data-entity-name");
    const mine_only = switchElement.checked;
    window.location.href = `/${entity_name}/ui?mine_only=${mine_only}`;
}

function onLogoutSuccess(response){
    if(response.status === "success"){
        showReloadModal({
            title: "Successfully Logged Out",
            seconds: 1,
            url:"/medperf_login"
        });
    }
    else{
        showErrorModal("Logout Failed", response);
    }
}

async function logout(){
    ajaxRequest(
        "/logout",
        "POST",
        null,
        onLogoutSuccess,
        "Error logging out:"
    )
    window.runningTaskId = await getTaskId();
}

function showCriticalPopup(data){
    const modalTitle = "Critical Warning";
    const modalTitleClasses = "fw-bold text-danger";
    const modalBody = `<p id="warning-text" class="fs-5 fw-bold text-danger">${data.message}</p>`;
    const modalFooter = `
    <button 
        id="acknowledge-btn" 
        type="button" 
        class="btn btn-success" 
        data-bs-dismiss="modal" 
        onclick="acknowledgeWarning(this);" 
        data-event-id="${data.id}"
    >
        Acknowledge
    </button>`;

    showModal({
        title: modalTitle,
        body: modalBody,
        footer: modalFooter,
        titleClasses: modalTitleClasses,
    });
}

function acknowledgeWarning(ackBtn){
    const eventId = ackBtn.getAttribute("data-event-id");
    const formData = new FormData();
    formData.append("event_id", eventId);
    
    ajaxRequest(
        "/events/acknowledge_event",
        "POST",
        formData,
        () => {},
        "Cannot acknowledge event:"
    )
}

function showModal({ title, body, footer="", titleClasses="", modalClasses="", extra_func=null }) {
    requestModal(() => { 
        resetModal();
        $("#page-modal-dialog").addClass(modalClasses);
        $("#page-modal-title")
            .attr("class", "")
            .addClass(titleClasses)
            .html(title);

        $("#page-modal-body").html(body);
        $("#page-modal-footer").html(footer);

        if (typeof extra_func === "function") {
            extra_func();
        }

        const modal = new bootstrap.Modal("#page-modal", {
            keyboard: false,
            backdrop: "static",
        });
        modal.show();
    });
}

function requestModal(showFn) {
    if (!window.modalOpen) {
        window.modalOpen = true;
        showFn();
    } else {
        window.modalQueue.push(showFn);
    }
}

function resetModal(){
    $("#page-modal-dialog").attr("class", "modal-dialog");
    $("#page-modal-title").attr("class", "modal-title fs-5").html("");
    $("#page-modal-body").html("");
    $("#page-modal-footer").html("");
}

let currentStageElement = null, logPanel, stagesList;
window.isPromptReceived = false;
window.onPromptComplete = null;
const logNodes = [];
window.modalQueue = [];
window.modalOpen = false;

$(document).ready(() => {
    applyDateFormatting();

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    
    window.notifications.forEach(notification => {
        addNotification(notification);
    });

    logPanel = document.getElementById('log-panel');
    stagesList = document.getElementById('stages-list');
    
    $("#respond-no-btn").on("click", () => respondToPrompt(false));
    $("#respond-yes-btn").on("click", () => respondToPrompt(true));

    $("#hide-yaml").on("click", (e) => {
        e.preventDefault();
        $("#yaml-panel").hide();
        $("#hide-yaml").hide();
    });

    $(".yaml-link").on("click", (e) => {
        e.preventDefault();
        const entity = $(e.currentTarget).data("entity");
        const id = $(e.currentTarget).data("id");
        const field = $(e.currentTarget).data("field");
        $("#yaml-panel").show();
        $(".detail-container").addClass("yaml-panel-visible");
        $("#loading-indicator").show();
        $("#yaml-code").hide();
        $.get("/fetch-yaml", {entity: entity, entity_uid: id, field_to_fetch: field}, function(data) {
            $("#yaml-code").html(data.content);
            Prism.highlightElement($("#yaml-code")[0]);
            $("#loading-indicator").hide();
            $("#yaml-code").show();
            $("#hide-yaml").show();
        }).fail(function(e) {
            $("#yaml-code").text(e.responseJSON.detail);
            $("#loading-indicator").hide();
            $("#yaml-code").show();
            $("#hide-yaml").show();
        });
    });

    $("#logout-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, logout, "logout?");
    });

    $("form").on("submit", (e) => {
        e.preventDefault();
    });

    document.addEventListener("hidden.bs.modal", function () {
        window.modalOpen = false;

        if (window.modalQueue.length > 0) {
            const nextModal = window.modalQueue.shift();
            window.modalOpen = true;
            nextModal();
        }
    });
});