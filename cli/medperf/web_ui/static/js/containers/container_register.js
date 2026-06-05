var REDIRECT_BASE = "/containers/ui/display/";

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
    var isValid = !!nameVal && containerPath.length > 0 && (isEncrypted === "true" ? decryptionPath.length > 0 : isEncrypted === "false");
    var btn = document.getElementById("register-container-btn");
    if (btn) btn.disabled = !isValid;
}

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
