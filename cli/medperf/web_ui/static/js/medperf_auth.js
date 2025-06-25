
function onMedperfLoginSuccess(response){
    if(response.status === "success"){
        showReloadModal("Successfully Logged In");
        timer(3, "/");
    }
    else{
        showErrorModal("Login Failed", response);
    }
}

async function medperfLogin(){
    addSpinner($("#medperf-login-btn")[0]);

    const formData = new FormData($("#medperf-login-form")[0]);
    
    disableElements("#medperf-login-form input, #medperf-login-form button");

    ajaxRequest(
        "/medperf_login",
        "POST",
        formData,
        onMedperfLoginSuccess,
        "Error while logging in:"
    );

    window.runningTaskId = await getTaskId();
    processLogin();
}

function handleLoginEvents(response){
    if (response.task_id !== window.runningTaskId){
        return;
    }

    if(response.type === "url"){
        $("#login-response").show();
        $("#link-text").show();
        document.getElementById("link").setAttribute("href", response.message);
        document.getElementById("link").innerHTML = response.message;
    }
    else if (response.type === "code"){
        $("#code-text").show();
        $("#code").html(response.message)
        $("#warning").show();
    }
}

function processLogin(){
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "/events",
            type: "GET",
            dataType: "json",
            success: function(response) {
                if (response.task_id === window.runningTaskId){
                    if (response.end){
                        resolve(response);
                        return;
                    }
                }
                handleLoginEvents(response);
                if(!window.isPromptReceived){
                    processLogin().then(resolve).catch(reject);
                }
            },
            error: function(xhr, status, error) {
                console.log("Error processLogin");
                console.log(xhr);
                console.log(status);
                console.log(error);
            }
        });
    });
}

function processPreviousLoginEvents(){
    if(window.previousEvents){
        window.previousEvents.forEach(event => {
            handleLoginEvents(event);
        });
    }
}

function resumeLogin(buttonSelector, callback){
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

    processPreviousLoginEvents();
    if(!window.isPromptReceived){
        processLogin().then(last_log => {
            callback(last_log.response);
        });
    }
}

function checkLoginFormValidity() {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const isValid = emailRegex.test($("#email").val());
    $("#medperf-login-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#medperf-login-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, medperfLogin, "want to login?");
    });

    $("#medperf-login-form input").on("keyup", checkLoginFormValidity);
});