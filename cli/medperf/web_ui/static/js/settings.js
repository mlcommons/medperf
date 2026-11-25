/** Show the configuration of a profile in the page modal. */
function showProfileModal(profileName, profileData) {
    var modalBody = "<h5 class=\"text-center text-lg font-bold mb-4\">Profile Name: " + escapeHtml(profileName) + "</h5><pre id=\"profile-yaml\" class=\"language-yaml overflow-x-auto p-4 rounded-lg bg-muted\">" + (profileData || "").replace(/</g, "&lt;") + "</pre>";
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\">Close</button>";
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

/** Activate the selected profile. */
function activateProfile(activateProfileBtn) {
    addSpinner(activateProfileBtn);
    var form = document.getElementById("profiles-form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#profiles-form select, #profiles-form button");
    disableElements(".profile-settings-form input, .profile-settings-form button, .profile-settings-form select");
    disableElements("#user-certificate button");
    ajaxRequest("/settings/activate_profile", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Profile Activated Successfully", seconds: 3 });
        else showErrorModal("Failed to Activate Profile", response);
    }, "Error activating profile:");
}

/** Show the configuration of the selected profile. */
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

/** Save the settings of the form holding the clicked Apply button. */
function editProfile(editProfileBtn) {
    var form = editProfileBtn.closest("form");
    var formData = form ? new FormData(form) : new FormData();
    disableElements("#profiles-form select, #profiles-form button");
    disableElements(".profile-settings-form input, .profile-settings-form button, .profile-settings-form select");
    disableElements("#user-certificate button");
    ajaxRequest("/settings/edit_profile", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Profile Settings Edited Successfully", seconds: 3 });
        else showErrorModal("Failed to Edit Profile Settings", response);
    }, "Error editing profile:");
}

/** The values a settings form would submit, to detect changes. */
function serializeSettingsForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
}

/** Enable a form's Apply button only if one of its settings changed. */
function checkForProfileEditChanges(form) {
    var btn = form.querySelector(".apply-settings-btn");
    if (btn) btn.disabled = serializeSettingsForm(form) === form.dataset.initialValues;
}

/**
 * Show the Slurm options when the Slurm switch is on, and the local options
 * (platform) when it is off. Slurm always uses the singularity platform.
 */
function updateLauncherFields() {
    var useSlurm = document.getElementById("use-slurm");
    if (!useSlurm) return;
    var slurm = useSlurm.checked;
    document.getElementById("launcher").value = slurm ? "slurm" : "local";
    document.getElementById("slurm-execution-fields").classList.toggle("hidden", !slurm);
    document.getElementById("local-execution-fields").classList.toggle("hidden", slurm);
    document.getElementById("launcher-mode").textContent = slurm ? "Slurm cluster" : "Local machine";
}

/**
 * The settings can only be edited for the active profile: show them (and
 * disable Activate) when the selected profile is the active one.
 */
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

/** Bind the settings page forms and buttons. */
function initSettings() {
    document.querySelectorAll("form.settings-action-form").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    var activateBtn = document.getElementById("activate-profile-btn");
    var viewBtn = document.getElementById("view-profile-btn");
    var profileEl = document.getElementById("profile");
    var useSlurm = document.getElementById("use-slurm");
    if (activateBtn) activateBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, activateProfile, "activate this profile?"); });
    if (viewBtn) viewBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, viewProfile, "view this profile?"); });
    if (profileEl) profileEl.addEventListener("change", checkProfileMatch);
    if (useSlurm) useSlurm.addEventListener("change", updateLauncherFields);
    updateLauncherFields();
    document.querySelectorAll(".profile-settings-form").forEach(function (form) {
        form.dataset.initialValues = serializeSettingsForm(form);
        var check = function () { checkForProfileEditChanges(form); };
        form.addEventListener("input", check);
        form.addEventListener("change", check);
        var applyBtn = form.querySelector(".apply-settings-btn");
        if (applyBtn) applyBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, editProfile, "edit this profile?"); });
        check();
    });
    checkProfileMatch();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSettings);
} else {
    initSettings();
}
