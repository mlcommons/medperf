var REDIRECT_BASE = "/assets/ui/display/";

function checkAssetFormValidity() {
    var nameVal = document.getElementById("name") ? document.getElementById("name").value.trim() : "";
    var isRemote = document.querySelector("input[name='asset_is_remote']:checked");
    var remoteVal = isRemote ? isRemote.value : "false";
    var assetURL = document.getElementById("asset-url") ? document.getElementById("asset-url").value.trim() : "";
    var assetPath = document.getElementById("asset-path") ? document.getElementById("asset-path").value.trim() : "";
    var isValid = !!nameVal && (remoteVal === "true" ? assetURL.length > 0 : remoteVal === "false" && assetPath.length > 0);
    var btn = document.getElementById("register-asset-btn");
    if (btn) btn.disabled = !isValid;
}

function initAssetRegister() {
    var form = document.getElementById("asset-register-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input").forEach(function (el) {
            el.addEventListener("keyup", checkAssetFormValidity);
            el.addEventListener("change", checkAssetFormValidity);
        });
    }
    var browseBtn = document.getElementById("browse-asset-btn");
    if (browseBtn) browseBtn.addEventListener("click", function () { browseWithFiles = true; browseFolderHandler("asset-path"); });
    document.querySelectorAll("input[name='asset_is_remote']").forEach(function (radio) {
        radio.addEventListener("change", function () {
            var urlContainer = document.getElementById("asset-url-container");
            var pathContainer = document.getElementById("asset-path-container");
            var assetUrlInput = document.getElementById("asset-url");
            var assetPathInput = document.getElementById("asset-path");
            if (this.value === "false") {
                if (urlContainer) urlContainer.classList.add("hidden");
                if (pathContainer) pathContainer.classList.remove("hidden");
                if (assetUrlInput) assetUrlInput.value = "";
            } else {
                if (pathContainer) pathContainer.classList.add("hidden");
                if (urlContainer) urlContainer.classList.remove("hidden");
                if (assetPathInput) assetPathInput.value = "";
            }
        });
    });
    checkAssetFormValidity();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAssetRegister);
} else {
    initAssetRegister();
}
