/*
 * Container registration page.
 */

var REDIRECT_BASE = "/containers/ui/display/";

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkContainerFormValidity() {
    var containerFileEl = document.getElementById("container-file");
    var containerPath = containerFileEl ? containerFileEl.value.trim() : "";
    if(window.ui_mode === window.evaluation_mode) {
        var checked = document.querySelector("input[name='model_encrypted']:checked");
        var isEncrypted = checked ? checked.value : "";
        var decryptionEl = document.getElementById("decryption-file");
        var decryptionPath = decryptionEl ? decryptionEl.value.trim() : "";
    } else {
        var isEncrypted = "false";
        var decryptionPath = "";
    }
    var nameEl = document.getElementById("name");
    var nameVal = nameEl ? nameEl.value.trim() : "";

    var problems = [];
    if (!nameVal) problems.push({ field: nameEl, message: "Enter the container name" });
    if (!containerPath) problems.push({ field: containerFileEl, message: "Enter the container config file path" });
    if (isEncrypted === "true") {
        if (!decryptionPath) problems.push({ field: decryptionEl, message: "Enter the decryption key file path" });
    } else if (isEncrypted !== "false") {
        problems.push({ field: null, message: "Choose whether the container is encrypted" });
    }

    var btn = document.getElementById("register-container-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the registration form and its path pickers. */
function init() {
    var form = document.getElementById("register-container-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input").forEach(function (el) {
            el.addEventListener("keyup", checkContainerFormValidity);
            el.addEventListener("change", checkContainerFormValidity);
        });
    }
    var browseDec = document.getElementById("browse-decryption-btn");
    if (browseDec) browseDec.addEventListener("click", function () { browseWithFiles = true; browseFolderHandler("decryption-file"); });
    document.querySelectorAll("input[name='model_encrypted']").forEach(function (radio) {
        radio.addEventListener("change", function () {
            var withEnc = document.getElementById("with-encryption");
            var decContainer = document.getElementById("decryption-file-container");
            var decFile = document.getElementById("decryption-file");
            if (withEnc && withEnc.checked) {
                if (decContainer) { decContainer.style.display = ""; decContainer.classList.remove("hidden"); }
            } else {
                if (decContainer) { decContainer.style.display = "none"; decContainer.classList.add("hidden"); }
                if (decFile) decFile.value = "";
            }
        });
    });
    var browseContainer = document.getElementById("browse-container-btn");
    if (browseContainer) browseContainer.addEventListener("click", function () { browseWithFiles = true; browseFolderHandler("container-file"); });
    var browseParams = document.getElementById("browse-parameters-btn");
    if (browseParams) browseParams.addEventListener("click", function () { browseWithFiles = true; browseFolderHandler("parameters-file"); });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
