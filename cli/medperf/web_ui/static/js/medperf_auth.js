
function onMedperfLoginSuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Successfully Logged In", seconds: 1, url: "/" });
    } else {
        showErrorModal("Login Failed", response);
    }
}

function medperfLogin(medperfLoginBtn) {
    addSpinner(medperfLoginBtn);
    var form = document.getElementById("medperf-login-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#medperf-login-form input, #medperf-login-form button");
    ajaxRequest("/medperf_login", "POST", formData, onMedperfLoginSuccess, "Error while logging in:");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function checkLoginFormValidity() {
    var emailInput = document.getElementById("email");
    var btn = document.getElementById("medperf-login-btn");
    if (!emailInput || !btn) return;
    var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    btn.disabled = !emailRegex.test(emailInput.value.trim());
}

function initMedperfAuth() {
    var loginBtn = document.getElementById("medperf-login-btn");
    var form = document.getElementById("medperf-login-form");
    if (loginBtn) {
        loginBtn.addEventListener("click", function (e) {
            var emailInput = form && form.querySelector("input");
            var email = emailInput ? emailInput.value : "";
            showConfirmModal(e.currentTarget, medperfLogin, "login as <strong>" + email + "</strong> ?");
        });
    }
    if (form) {
        var input = form.querySelector("input");
        if (input) input.addEventListener("keyup", checkLoginFormValidity);
    }
    checkLoginFormValidity();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMedperfAuth);
} else {
    initMedperfAuth();
}
