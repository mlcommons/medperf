function init() {
    document.querySelectorAll('form[id^="container-association-form-"]').forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
