function onContainerRegisterSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Model Registered Successfully", seconds: 3, url: "/containers/ui/display/" + response.container_id });
    } else {
        showErrorModal("Failed to Register Model", response);
    }
}

function registerContainer(registerButton) {
    addSpinner(registerButton);
    var form = document.getElementById("container-register-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#container-register-form input, #container-register-form button");
    ajaxRequest("/containers/register", "POST", formData, onContainerRegisterSuccess, "Error registering container:");
    showPanel("Registering Container...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function checkContainerFormValidity() {
    var containerFileEl = document.getElementById("container-file");
    var containerPath = containerFileEl ? containerFileEl.value.trim() : "";
    var checked = document.querySelector("input[name='model_encrypted']:checked");
    var isEncrypted = checked ? checked.value : "";
    var decryptionEl = document.getElementById("decryption-file");
    var decryptionPath = decryptionEl ? decryptionEl.value.trim() : "";
    var nameEl = document.getElementById("name");
    var nameVal = nameEl ? nameEl.value.trim() : "";
    var isValid = !!nameVal && containerPath.length > 0 && (isEncrypted === "true" ? decryptionPath.length > 0 : isEncrypted === "false");
    var btn = document.getElementById("register-container-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var btn = document.getElementById("register-container-btn");
    if (btn) btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, registerContainer, "register this container?"); });
    var form = document.getElementById("container-register-form");
    if (form) form.querySelectorAll("input").forEach(function (el) {
        el.addEventListener("keyup", checkContainerFormValidity);
        el.addEventListener("change", checkContainerFormValidity);
    });
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
    checkContainerFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
