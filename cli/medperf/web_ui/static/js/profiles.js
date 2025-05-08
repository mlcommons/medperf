
function activateProfile(activateProfileBtn) {
    const formData = new FormData($("#profiles-form")[0]);
    
    disableElements("#profiles-form select, #profiles-form button");

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
            }
            else {
                showErrorModal("Failed to Get Profile Details", response);
            }
        },
        "Error viewing profile:"
    );
}


$(document).ready(() => {
    $("#activate-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, activateProfile, "activate this profile?");
    });

    $("#view-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, viewProfile, "view this profile?");
    });
});