var REDIRECT_BASE = "/models/ui/display/";

// What a model owner is agreeing to when they start a confidential run: a
// machine of their own goes up in their cloud account, and the results are
// encrypted for whoever the two asset owners agreed to release them to -- who
// is usually the data owner, not them.
function showRunConfirmModal(form, callback) {
    var modalBody = [
        "<p id=\"confirm-text\" class=\"text-lg\">You are going to run this model, and this will incur costs to your cloud provider.",
        " You may not be able to immediately see the results. Are you sure?</p>"
    ].join("");
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-secondary close-modal-btn\">Cancel</button><button id=\"confirmation-btn\" type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\">Run</button>";
    var extra = function () {
        var confirmBtn = document.getElementById("confirmation-btn");
        if (confirmBtn) confirmBtn.addEventListener("click", function () {
            callback(form);
            window.hidePageModal();
            window.onModalHidden();
        });
        document.querySelectorAll(".close-modal-btn").forEach(function (btn) {
            if (btn.id !== "confirmation-btn") btn.addEventListener("click", function () { window.hidePageModal(); window.onModalHidden(); });
        });
    };
    showModal({ title: "Confirm confidential run", body: modalBody, footer: modalFooter, extra_func: extra });
}

function submitRunForm(e) {
    e.preventDefault();
    showRunConfirmModal(e.target, submitActionFormWithForm);
}

function initModelDetail() {
    document.querySelectorAll("form.model-action-form").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    document.querySelectorAll("form.model-run-form").forEach(function (form) {
        form.addEventListener("submit", submitRunForm);
    });
    document.querySelectorAll("[id^='show-']").forEach(function (el) {
        el.addEventListener("click", function () { showResult(el); });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initModelDetail);
} else {
    initModelDetail();
}
