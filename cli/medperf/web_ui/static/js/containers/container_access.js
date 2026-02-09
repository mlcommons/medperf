function getEmailsList(element) {
    var emailsArr = [];
    if (!element) return emailsArr;
    element.querySelectorAll(".email-chip").forEach(function (chip) {
        emailsArr.push((chip.textContent || "").replace(/\s*×\s*$/, "").trim());
    });
    return emailsArr;
}

function createEmailChip(email, inputElement) {
    var chip = document.createElement("div");
    chip.className = "email-chip inline-block bg-gray-200 dark:bg-gray-600 rounded-full py-1 px-3 mr-2 mb-2 text-sm";
    chip.textContent = email;
    var remove = document.createElement("span");
    remove.className = "remove-btn ml-2 cursor-pointer font-bold";
    remove.textContent = "×";
    remove.addEventListener("click", function () { chip.remove(); });
    chip.appendChild(remove);
    if (inputElement && inputElement.parentNode) inputElement.parentNode.insertBefore(chip, inputElement);
}

function parseEmails(element) {
    if (!element || !element.getAttribute) return;
    var raw = element.getAttribute("data-allowed-list") || "[]";
    try {
        var jsonList = JSON.parse(raw);
        var inputEl = element.querySelector("input");
        jsonList.forEach(function (email) { createEmailChip(email, inputEl); });
    } catch (_) {}
}

function checkAccessForm() {
    var allowListArr = getEmailsList(document.getElementById("allowed-email-list"));
    if (!document.getElementById("benchmark") || !document.getElementById("benchmark").value) {
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    if (!allowListArr.length) {
        showErrorToast("Make sure that the email allow list is not empty");
        return false;
    }
    return true;
}

function checkAutoAccessForm() {
    var allowListArr = getEmailsList(document.getElementById("allowed-email-list-auto"));
    if (!document.getElementById("benchmark-auto") || !document.getElementById("benchmark-auto").value) {
        showErrorToast("Make sure that you've selected a benchmark");
        return false;
    }
    var intervalEl = document.getElementById("interval-auto");
    var interval = intervalEl ? Number(intervalEl.value) : 0;
    if (!interval || interval < 5 || interval > 60) {
        showErrorToast("Make sure that the time interval is between 5 and 60 (inclusive)");
        return false;
    }
    if (!allowListArr.length) {
        showErrorToast("Make sure that the email allow list is not empty");
        return false;
    }
    return true;
}

function onGrantAccessSuccess(response) {
    if (response && response.status === "success") showReloadModal({ title: "Successfully Granted Access to the Selected Users", seconds: 3 });
    else showErrorModal("Failed to Grant Access", response);
}

function grantAccess(grantBtn) {
    addSpinner(grantBtn);
    disableElements(".card button, .card input, .card select");
    var allowListArr = getEmailsList(document.getElementById("allowed-email-list"));
    var formData = new FormData();
    formData.append("benchmark_id", document.getElementById("benchmark").value);
    formData.append("model_id", grantBtn.getAttribute("data-model-id"));
    formData.append("emails", allowListArr.join(" "));
    ajaxRequest("/containers/grant_access", "POST", formData, onGrantAccessSuccess, "Failed to grant access");
    showPanel("Granting Access...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function startAutoGrant(startBtn) {
    disableElements(".card button, .card input, .card select");
    var allowListArr = getEmailsList(document.getElementById("allowed-email-list-auto"));
    var formData = new FormData();
    formData.append("benchmark_id", document.getElementById("benchmark-auto").value);
    formData.append("model_id", startBtn.getAttribute("data-model-id"));
    formData.append("interval", document.getElementById("interval-auto").value);
    formData.append("emails", allowListArr.join(" "));
    ajaxRequest("/containers/start_auto_access", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Successfully Started Auto Grant Access", seconds: 2 });
        else showErrorModal("Failed to Start Auto Grant Access", response);
    }, "Failed to start auto grant access");
}

function stopAutoGrant(stopBtn) {
    disableElements(".card button, .card input, .card select");
    var formData = new FormData();
    formData.append("model_id", stopBtn.getAttribute("data-model-id"));
    ajaxRequest("/containers/stop_auto_access", "POST", formData, function (response) {
        if (response && response.status === "success") showReloadModal({ title: "Successfully Stopped Auto Grant Access", seconds: 2 });
        else showErrorModal("Failed to Stop Auto Grant Access", response);
    }, "Failed to stop auto grant access");
}

function onrevokeUserAccessSuccess(response) {
    if (response && response.status === "success") showReloadModal({ title: "Successfully Revoked User Access", seconds: 3 });
    else showErrorModal("Failed to Revoke User Access", response);
}

function revokeUserAccess(revokeAccessBtn) {
    addSpinner(revokeAccessBtn);
    disableElements(".card button, .card input, .card select");
    var formData = new FormData();
    formData.append("model_id", revokeAccessBtn.getAttribute("data-model-id"));
    formData.append("key_id", revokeAccessBtn.getAttribute("data-key-id"));
    ajaxRequest("/containers/revoke_user_access", "POST", formData, onDeleteKeysSuccess, "Failed to revoke user access");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function onDeleteKeysSuccess(response) {
    if (response && response.status === "success") showReloadModal({ title: "Successfully Deleted Keys", seconds: 3 });
    else showErrorModal("Failed to Delete Keys", response);
}

function deleteKeys(deleteKeysBtn) {
    addSpinner(deleteKeysBtn);
    disableElements(".card button, .card input, .card select");
    var formData = new FormData();
    formData.append("model_id", deleteKeysBtn.getAttribute("data-model-id"));
    ajaxRequest("/containers/delete_keys", "POST", formData, onDeleteKeysSuccess, "Failed to delete keys");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function showErrorToast(message) {
    showToast("Validation Error", message, "text-bg-danger");
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function init() {
    parseEmails(document.getElementById("allowed-email-list"));
    parseEmails(document.getElementById("allowed-email-list-auto"));
    document.querySelectorAll(".email-input").forEach(function (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " " || e.key === ",") {
                e.preventDefault();
                var email = this.value.trim().replace(/,$/, "");
                if (email && isValidEmail(email)) { createEmailChip(email, this); this.value = ""; }
            }
        });
        input.addEventListener("paste", function (e) {
            e.preventDefault();
            var clipboardData = (e.clipboardData || window.clipboardData).getData("text");
            clipboardData.split(/[\s,]+/).forEach(function (email) {
                email = email.trim();
                if (email && isValidEmail(email)) createEmailChip(email, input);
            });
            input.value = "";
        });
    });
    var grantBtn = document.getElementById("grant-access-btn");
    if (grantBtn) grantBtn.addEventListener("click", function (e) {
        if (checkAccessForm()) showConfirmModal(e.currentTarget, grantAccess, "grant access to the emails added?");
    });
    var startBtn = document.getElementById("start-auto-access-btn");
    if (startBtn) startBtn.addEventListener("click", function (e) {
        if (checkAutoAccessForm()) showConfirmModal(e.currentTarget, startAutoGrant, "start automatic grant access for the selected benchmark?");
    });
    var stopBtn = document.getElementById("stop-auto-access-btn");
    if (stopBtn) stopBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, stopAutoGrant, "stop automatic grant access?"); });
    document.querySelectorAll(".revoke-access-btn").forEach(function (btn) {
        btn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, revokeUserAccess, "revoke access for the selected user?"); });
    });
    var deleteKeysBtn = document.getElementById("delete-keys-btn");
    if (deleteKeysBtn) deleteKeysBtn.addEventListener("click", function (e) { showConfirmModal(e.currentTarget, deleteKeys, "delete all keys?"); });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
