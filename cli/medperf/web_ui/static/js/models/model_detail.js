var REDIRECT_BASE = "/models/ui/display/";

function initModelDetail() {
    document.querySelectorAll("form.model-action-form").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initModelDetail);
} else {
    initModelDetail();
}
