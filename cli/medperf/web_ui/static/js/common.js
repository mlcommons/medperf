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

function showReloadModal(title){
    $("#popup-modal-title").html(title);
    const popupModal = new bootstrap.Modal("#popup-modal", {
        keyboard: false,
        backdrop: "static"
    })
    popupModal.show();
}

function timer(seconds, url=null){
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
    let responseError = response.error;
    let responseStatus = response.status;
    let errorText = "";
    if (responseError){
        errorText += responseError.replace("\n", "<br>") + "<br>";
    }
    if (responseStatus){
        errorText += responseStatus.replace("\n", "<br>");
    }
    $("#error-modal-title").html(errorTitle);
    $("#error-text").html(errorText);
    const errorModal = new bootstrap.Modal("#error-modal", {
        keyboard: false,
        backdrop: "static"
    });
    errorModal.show();
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
    getEvents(logPanel, stagesList, currentStageElement).then((last_log) => {
        if (typeof window.onPromptComplete === "function") {
            window.onPromptComplete(last_log);
        }
    });
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

    currentStageElement = processPreviousEvents(logPanel, stagesList, currentStageElement);
    window.onPromptComplete = (last_log) => {
        callback(last_log.response);
    };
    if(!window.isPromptReceived){
        getEvents(logPanel, stagesList, currentStageElement).then(last_log => {
            callback(last_log.response);
        });
    }
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
        showReloadModal("Successfully Logged Out");
        timer(3, url="/medperf_login");
    }
    else{
        showErrorModal("Logout Failed", response);
    }
}

function logout(){
    ajaxRequest(
        "/logout",
        "POST",
        null,
        onLogoutSuccess,
        "Error logging out:"
    )
}

let currentStageElement = null, logPanel, stagesList;
window.isPromptReceived = false;

$(document).ready(() => {
    applyDateFormatting();

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    
    window.onPromptComplete = null;
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
        }).fail(function() {
            $("#yaml-code").text("Failed to load content");
            $("#loading-indicator").hide();
            $("#yaml-code").show();
            $("#hide-yaml").show();
        });
    });

    $("form").on("submit", (e) => {
        e.preventDefault();
    });
});