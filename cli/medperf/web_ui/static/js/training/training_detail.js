var REDIRECT_BASE = "/training/ui/display/";

function init() {
    var browseSetPlanBtn = document.getElementById("browse-set-plan-btn");
    if (browseSetPlanBtn) {
        browseSetPlanBtn.addEventListener("click", function () {
            if (typeof browseFolderHandler === "function") {
                browseWithFiles = true;
                browseFolderHandler("set-plan-path");
            }
        });
    }
    var browseStartEventParticipantsBtn = document.getElementById("browse-start-event-participants-btn");
    if (browseStartEventParticipantsBtn) {
        browseStartEventParticipantsBtn.addEventListener("click", function () {
            if (typeof browseFolderHandler === "function") {
                browseWithFiles = true;
                browseFolderHandler("start-event-participants-path");
            }
        });
    }

    var actionForms = document.querySelectorAll(
        '#set-plan-form, #update-plan-form, #start-event-form, #close-event-form, #get-status-form, ' +
        '#set-aggregator-form, .training-approve-reject-form'
    );

    actionForms.forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
