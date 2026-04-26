function showProfileModal(profileName, profileData) {
    var modalBody = "<h5 class=\"text-center text-lg font-bold mb-4\">Profile Name: " + profileName + "</h5><pre id=\"profile-yaml\" class=\"language-yaml overflow-x-auto p-4 rounded-lg bg-gray-100 dark:bg-gray-700\">" + (profileData || "").replace(/</g, "&lt;") + "</pre>";
    var modalFooter = "<button type=\"button\" class=\"px-4 py-2 rounded-xl medperf-bg dark:bg-green-600 text-white font-semibold close-modal-btn\">Close</button>";
    var extra = function () {
        var el = document.getElementById("profile-yaml");
        if (window.Prism && el) Prism.highlightElement(el);
    };
    showModal({
        title: "View Profile",
        body: modalBody,
        footer: modalFooter,
        modalClasses: "max-w-4xl w-full",
        extra_func: extra
    });
}

function activateProfile(activateProfileBtn) {
    addSpinner(activateProfileBtn);
    var form = document.getElementById("profiles-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button, #edit-config-form select");
    disableElements("#user-certificate button");
    ajaxRequest("/settings/activate_profile", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Profile Activated Successfully", seconds: 3 });
        else showErrorModal("Failed to Activate Profile", response);
    }, "Error activating profile:");
}

function viewProfile(viewProfileBtn) {
    var form = document.getElementById("profiles-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#profiles-form select, #profiles-form button");
    ajaxRequest("/settings/view_profile", "POST", formData, function (response) {
        if (response && response.status === "success") {
            showProfileModal(response.profile, response.profile_dict);
            enableElements("#profiles-form select, #profiles-form button");
            checkProfileMatch();
        } else showErrorModal("Failed to Get Profile Details", response);
    }, "Error viewing profile:");
}

function editProfile(editProfileBtn) {
    var form = document.getElementById("edit-config-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button, #edit-config-form select");
    disableElements("#user-certificate button");
    ajaxRequest("/settings/edit_profile", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Profile Settings Edited Successfully", seconds: 3 });
        else showErrorModal("Failed to Edit Profile Settings", response);
    }, "Error editing profile:");
}

function checkForProfileEditChanges() {
    var gpusEl = document.getElementById("gpus");
    var platformEl = document.getElementById("platform");
    var caEl = document.getElementById("ca");
    var fingerprintEl = document.getElementById("fingerprint");
    var gpusVal = gpusEl ? gpusEl.value : "";
    var platformVal = platformEl ? platformEl.value : "";
    var caVal = caEl ? caEl.value : "";
    var fingerprintVal = fingerprintEl ? fingerprintEl.value : "";
    var gpusChanged = gpusVal !== window.currentSettings.defaultGpus;
    var platformChanged = platformVal !== window.currentSettings.defaultPlatform;
    var caChanged = caVal !== window.currentSettings.defaultCA;
    var fingerprintChanged = fingerprintVal !== window.currentSettings.defaultFingerprint;
    var btn = document.getElementById("apply-profile-changes-btn");
    if (btn) btn.disabled = !(gpusChanged || platformChanged || caChanged || fingerprintChanged);
}

function checkProfileMatch() {
    var profileEl = document.getElementById("profile");
    var selectedProfile = profileEl ? profileEl.value : "";
    var editContainer = document.getElementById("edit-config-container");
    var activateBtn = document.getElementById("activate-profile-btn");
    if (selectedProfile === window.currentSettings.activeProfile) {
        if (editContainer) { editContainer.style.display = ""; editContainer.classList.remove("hidden"); }
        if (activateBtn) activateBtn.disabled = true;
    } else {
        if (editContainer) { editContainer.style.display = "none"; editContainer.classList.add("hidden"); }
        if (activateBtn) activateBtn.disabled = false;
    }
}

function initSettings() {
    document.querySelectorAll("form.settings-action-form").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    var activateBtn = document.getElementById("activate-profile-btn");
    var viewBtn = document.getElementById("view-profile-btn");
    var applyBtn = document.getElementById("apply-profile-changes-btn");
    var profileEl = document.getElementById("profile");
    if (activateBtn) activateBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, activateProfile, "activate this profile?"); });
    if (viewBtn) viewBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, viewProfile, "view this profile?"); });
    if (applyBtn) applyBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, editProfile, "edit this profile?"); });
    if (profileEl) profileEl.addEventListener("change", checkProfileMatch);
    document.querySelectorAll("#gpus, #platform, #ca, #fingerprint").forEach(function (el) {
        if (el) el.addEventListener("input", checkForProfileEditChanges);
    });
    checkProfileMatch();
    checkForProfileEditChanges();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSettings);
} else {
    initSettings();
}
