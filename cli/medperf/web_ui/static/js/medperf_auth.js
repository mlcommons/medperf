/*
 * MedPerf login page.
 */

/** Handle the login response. */
function onLoginSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Logged in successfully", seconds: 3, url: "/" });
    } else {
        showErrorModal("Login Failed", response);
    }
}

/** Enable the Sign In button only for a valid email, and tell the user why otherwise (see form_validation.js). */
function checkLoginFormValidity() {
    var emailInput = document.getElementById("email");
    var btn = document.getElementById("medperf-login-btn");
    if (!emailInput || !btn) return;
    var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    var email = emailInput.value.trim();
    var problems = [];
    if (!email) problems.push({ field: emailInput, message: "Enter your email" });
    else if (!emailRegex.test(email)) problems.push({ field: emailInput, message: "Enter a valid email address (e.g. name@example.com)" });
    btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the login form. */
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
