function showProfileModal(profileName, profileData){

    const modalTitle = "View Profile";
    const modalBody = `
    <h5 class="text-center">Profile Name: ${profileName}</h5>
    <pre id="profile-yaml" class="language-yaml">${profileData}</pre>
    `;
    const modalFooter = '<button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>';
    const extra_fn = () => { Prism.highlightElement($("#profile-yaml")[0]); };

    showModal({
        title: modalTitle,
        body: modalBody,
        footer: modalFooter,
        modalClasses: "modal-lg",
        extra_func: extra_fn
    });
}


function activateProfile(activateProfileBtn) {
    addSpinner(activateProfileBtn);

    const formData = new FormData($("#profiles-form")[0]);
    
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#user-certificate button");
    
    ajaxRequest(
        "/settings/activate_profile",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal({
                    title: "Profile Activated Successfully",
                    seconds: 3
                });
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
        "/settings/view_profile",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                const profileName = response.profile;
                const profileData = response.profile_dict;

                showProfileModal(profileName, profileData);

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

    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#user-certificate button");

    ajaxRequest(
        "/settings/edit_profile",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal({
                    title: "Profile Edited Successfully",
                    seconds: 3
                });
            }
            else {
                showErrorModal("Failed to Edit Profile", response);
            }
        },
        "Error editing profile:"
    );
}

function editCertificate(editCertBtn) {
    const formData = new FormData($("#edit-certs-form")[0]);

    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#user-certificate button");

    ajaxRequest(
        "/settings/edit_certificate",
        "POST",
        formData,
        (response) => {
            if (response.status === "success"){
                showReloadModal({
                    title: "Certificate Settings Edited Successfully",
                    seconds: 3
                });
            }
            else {
                showErrorModal("Failed to Edit Certificate Settings", response);
            }
        },
        "Error editing certificate settings:"
    );
}

function onGetCertSuccess(response){
    if (response.status === "success"){
        showReloadModal({
            title: "Certificate Retrieved Successfully",
            seconds: 3
        });
    }
    else {
        showErrorModal("Failed to Get Certificate", response);
    }
}

function onDeleteCertSuccess(response){
    if (response.status === "success"){
        showReloadModal({
            title: "Certificate Deleted Successfully",
            seconds: 3
        });
    }
    else {
        showErrorModal("Failed to Delete Certificate", response);
    }
}

function onSubmitCertSuccess(response){
    if (response.status === "success"){
        showReloadModal({
            title: "Certificate Submitted Successfully",
            seconds: 3
        });
    }
    else {
        showErrorModal("Failed to Submit Certificate", response);
    }
}

async function getCertificate(getCertBtn){
    addSpinner(getCertBtn);

    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#certificate-status button");

    ajaxRequest(
        "/settings/get_certificate",
        "POST",
        null,
        onGetCertSuccess,
        "Error getting certificate:"
    );

    showPanel(`Getting Client Certificate...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

async function deleteCertificate(deleteCertBtn){
    addSpinner(deleteCertBtn);

    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#certificate-status button");

    ajaxRequest(
        "/settings/delete_certificate",
        "POST",
        null,
        onDeleteCertSuccess,
        "Error deleting certificate:"
    );

    showPanel(`Deleting Client Certificate...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

async function submitCertificate(submitCertBtn){
    addSpinner(submitCertBtn);
    
    disableElements("#profiles-form select, #profiles-form button");
    disableElements("#edit-config-form input, #edit-config-form button");
    disableElements("#edit-certs-form input, #edit-certs-form select, #edit-certs-form button");
    disableElements("#certificate-status button");

    ajaxRequest(
        "/settings/submit_certificate",
        "POST",
        null,
        onSubmitCertSuccess,
        "Error submitting certificate:"
    );

    showPanel(`Submitting Client Certificate...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkForProfileEditChanges() {
    const gpusVal = $('#gpus').val();
    const platformVal = $('#platform').val();

    const gpusChanged = gpusVal !== window.currentSettings.defaultGpus;
    const platformChanged = platformVal !== window.currentSettings.defaultPlatform;

    $('#apply-profile-changes-btn').prop('disabled', !(gpusChanged || platformChanged));
}

function checkProfileMatch() {
    const selectedProfile = $('#profile').val();

    if (selectedProfile === window.currentSettings.activeProfile) {
        $('#edit-config-container').show();
        $('#edit-certs-container').show();
        $('#activate-profile-btn').prop('disabled', true);
    } else {
        $('#edit-config-container').hide();
        $('#edit-certs-container').hide();
        $('#activate-profile-btn').prop('disabled', false);
    }
}

function checkForCertificateEditChanges() {
    const caVal = $('#ca').val();
    const fingerprintVal = $('#fingerprint').val().trim();

    const caChanged = caVal !== window.currentSettings.defaultCA;
    const fingerprintChanged = fingerprintVal !== window.currentSettings.defaultFingerprint;

    $('#apply-cert-changes-btn').prop('disabled', !(caChanged || fingerprintChanged));
}

$(document).ready(() => {
    $("#activate-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, activateProfile, "activate this profile?");
    });

    $("#view-profile-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, viewProfile, "view this profile?");
    });

    $("#apply-profile-changes-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editProfile, "edit this profile?");
    });

    $("#apply-cert-changes-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, editCertificate, "modify certificate settings?");
    });

    $("#get-cert-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, getCertificate, "get a new certificate?");
    });

    $("#delete-cert-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, deleteCertificate, "delete the certificate?");
    });

    $("#submit-cert-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, submitCertificate, "submit the certificate?");
    });

    $('#profile').on('change', checkProfileMatch);
    $('#gpus, #platform').on('input', checkForProfileEditChanges);
    $('#ca, #fingerprint').on('input', checkForCertificateEditChanges);

    // Run initial state checks
    checkProfileMatch();
    checkForProfileEditChanges();
    checkForCertificateEditChanges();
});