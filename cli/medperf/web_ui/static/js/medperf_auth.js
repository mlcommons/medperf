
function onLoginSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Logged in successfully", seconds: 3, url: "/" });
    } else {
        showErrorModal("Login Failed", response);
    }
}

function checkLoginFormValidity() {
    var emailInput = document.getElementById("email");
    var btn = document.getElementById("medperf-login-btn");
    if (!emailInput || !btn) return;
    var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    btn.disabled = !emailRegex.test(emailInput.value.trim());
}

function init() {
    var form = document.getElementById("medperf-login-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        const emailInput = document.getElementById("email");
        if (emailInput) emailInput.addEventListener("keyup", checkLoginFormValidity);
    }
    checkLoginFormValidity();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
