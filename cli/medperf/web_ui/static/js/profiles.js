
function activateProfile(activateProfileBtn) {
    addSpinner(activateProfileBtn);

    const formData = new FormData($("#profiles-form")[0]);
    
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    ajaxRequest(
        "/profiles/activate",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal("Profile Activated Successfully");
                timer(3);
            }
            else {
                showErrorModal("Failed to Activate Profile", response);
            }
        },
        "Error activating profile:"
    );
}

function viewProfile(viewProfileBtn){
    const formData = new FormData($("#profiles-form")[0]);
    
    disableElements("#profiles-form select, #profiles-form button");

    ajaxRequest(
        "/profiles/view",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                $("#view-profile-modal-title").html("View Profile");
                $("#view-profile-name").text("Profile Name: "+ response.profile);
                $("#profile-yaml").html(response.profile_dict);
                Prism.highlightElement(document.getElementById("profile-yaml"));

                $("#view-profile-modal").modal("show");
                
                enableElements("#profiles-form select, #profiles-form button");
                checkProfileMatch();
            }
            else {
                showErrorModal("Failed to Get Profile Details", response);
            }
        },
        "Error viewing profile:"
    );
}

function editProfile(editProfileBtn) {
    const formData = new FormData($("#edit-config-form")[0]);

    disableElements("#edit-config-form input, #edit-config-form button");

    ajaxRequest(
        "/profiles/edit",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal("Profile Edited Successfully");
                timer(3);
            }
            else {
                showErrorModal("Failed to Edit Profile", response);
            }
        },
        "Error editing profile:"
    );
}

function checkForEditChanges() {
    const gpusVal = $('#gpus').val();
    const platformVal = $('#platform').val();

    const gpusChanged = gpusVal !== window.defaultGpus;
    const platformChanged = platformVal !== window.defaultPlatform;

    $('#apply-changes-btn').prop('disabled', !(gpusChanged || platformChanged));
}

function checkProfileMatch() {
    const selectedProfile = $('#profile').val();

    if (selectedProfile === window.activeProfile) {
        $('#edit-config-container').show();
        $('#activate-profile-btn').prop('disabled', true);
    } else {
        $('#edit-config-container').hide();
        $('#activate-profile-btn').prop('disabled', false);
    }
}

$(document).ready(() => {
    $("#activate-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, activateProfile, "activate this profile?");
    });

    $("#view-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, viewProfile, "view this profile?");
    });

    $("#apply-changes-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editProfile, "edit this profile?");
    });

    $('#profile').on('change', checkProfileMatch);
    $('#gpus, #platform').on('input', checkForEditChanges);

    // Run initial state checks
    checkProfileMatch();
    checkForEditChanges();
});