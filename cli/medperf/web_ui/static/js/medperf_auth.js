
function onMedperfLoginSuccess(response){
    if(response.status === "success"){
        showReloadModal("Successfully Logged In");
        timer(3, "/");
    }
    else{
        showErrorModal("Login Failed", response);
    }
}

async function medperfLogin(medperfLoginBtn){
    addSpinner(medperfLoginBtn);

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
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkLoginFormValidity() {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const isValid = emailRegex.test($("#email").val());
    $("#medperf-login-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#medperf-login-btn").on("click", (e) => {
        let email =  $("#medperf-login-form input").val()
        showConfirmModal(e.currentTarget, medperfLogin, `want to login as <strong>${email}</strong> ?`);
    });

    $("#medperf-login-form input").on("keyup", checkLoginFormValidity);
});