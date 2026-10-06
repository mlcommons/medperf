/*
 * Asset registration page (local or remote asset).
 */

var REDIRECT_BASE = "/assets/ui/display/";

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkAssetFormValidity() {
    var nameEl = document.getElementById("name");
    var isRemote = document.querySelector("input[name='asset_is_remote']:checked");
    var remoteVal = isRemote ? isRemote.value : "false";

    var problems = [];
    requireValue(problems, nameEl, "Enter the asset name");
    if (remoteVal === "true") requireValue(problems, document.getElementById("asset-url"), "Enter the asset URL");
    else requireValue(problems, document.getElementById("asset-path"), "Enter the asset path");

    var btn = document.getElementById("register-asset-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the registration form, and switch between local and remote asset inputs. */
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
