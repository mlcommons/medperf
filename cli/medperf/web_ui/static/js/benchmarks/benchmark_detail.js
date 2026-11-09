/*
 * Benchmark details page: associations policy, committee members, results
 * and the preparation dashboard form.
 */

var REDIRECT_BASE = "/benchmarks/ui/display/";

/**
 * Confirmation message of the policy update. An empty allow list auto-approves
 * nobody: it is refused when the saved list is already empty, otherwise (the
 * user is emptying it) the mode will be set to Never. Null when refused.
 */
function buildAssociationsPolicyConfirmMessage(message) {
    var notes = [];
    var kinds = ["dataset", "model"];
    for (var i = 0; i < kinds.length; i++) {
        var kind = kinds[i];
        var modeEl = document.getElementById(kind + "-auto-approve-mode");
        if (!modeEl || modeEl.value !== "ALLOWLIST") continue;
        var listEl = document.getElementById(kind + "-allow-list-emails");
        if (getEmailsList(listEl).length) continue;
        if (!getSavedEmails(listEl).length) {
            showErrorToast("The " + kind + " allow list is empty. Add at least one email, or choose another mode.");
            return null;
        }
        notes.push("This will empty the " + kind + " allow list and set the " + kind + " auto approve mode to Never.");
    }
    if (!notes.length) return message;
    return message + " <strong>" + notes.join(" ") + "</strong>";
}

/**
 * Confirmation message of the committee members update. An empty list removes
 * all the members: it is refused when the committee is already empty. Null
 * when refused.
 */
function buildCommitteeMembersConfirmMessage(message) {
    var listEl = document.getElementById("committee-members-emails");
    if (getEmailsList(listEl).length) return message;
    if (!getSavedEmails(listEl).length) {
        showErrorToast("The committee members list is empty. Add at least one email.");
        return null;
    }
    return message + " <strong>This will remove all committee members.</strong>";
}

/** Handle the response of updating the associations policy. */
function onUpdateAssociationsPolicySuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Benchmark Associations Policy Successfully Updated", seconds: 3 });
    } else {
        showErrorModal("Failed to Update Benchmark Associations Policy", response);
    }
}

/** Save the associations policy (auto-approval modes and allow lists). */
function updateAssociationsPolicy(saveBtn) {
    addSpinner(saveBtn);
    disableElements("#association-policy-form button, #association-policy-form input, #association-policy-form select");
    var datasetModeEl = document.getElementById("dataset-auto-approve-mode");
    var modelModeEl = document.getElementById("model-auto-approve-mode");
    var datasetApproveMode = datasetModeEl ? datasetModeEl.value : "NEVER";
    var modelApproveMode = modelModeEl ? modelModeEl.value : "NEVER";
    var formData = new FormData();
    if (datasetApproveMode === "ALLOWLIST") {
        var datasetAllowListArr = getEmailsList(document.getElementById("dataset-allow-list-emails"));
        formData.append("dataset_emails", datasetAllowListArr.join(" "));
    }
    if (modelApproveMode === "ALLOWLIST") {
        var modelAllowListArr = getEmailsList(document.getElementById("model-allow-list-emails"));
        formData.append("model_emails", modelAllowListArr.join(" "));
    }
    formData.append("benchmark_id", saveBtn.getAttribute("data-benchmark-id"));
    formData.append("dataset_mode", datasetApproveMode);
    formData.append("model_mode", modelApproveMode);
    ajaxRequest("/benchmarks/update_associations_policy", "POST", formData, onUpdateAssociationsPolicySuccess, "Failed to update associations policy");
}

/** Handle the response of updating the committee members. */
function onUpdateCommitteeMembersSuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Benchmark Committee Members Successfully Updated", seconds: 3 });
    } else {
        showErrorModal("Failed to Update Benchmark Committee Members", response);
    }
}

/** Save the committee members emails. */
function updateCommitteeMembers(saveBtn) {
    addSpinner(saveBtn);
    disableElements("#committee-members-form button, #committee-members-form input");
    var committeeEmailsArr = getEmailsList(document.getElementById("committee-members-emails"));
    var formData = new FormData();
    formData.append("committee_emails", committeeEmailsArr.join(" "));
    formData.append("benchmark_id", saveBtn.getAttribute("data-benchmark-id"));
    ajaxRequest("/benchmarks/update_committee_members", "POST", formData, onUpdateCommitteeMembersSuccess, "Failed to update committee members");
}

/** Bind the page forms, email lists, results and dashboard form. */
function initBenchmarkDetail() {
    document.querySelectorAll("form.benchmark-action-form").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    document.querySelectorAll("[id^='show-']").forEach(function (el) {
        el.addEventListener("click", function () { showResult(el); });
    });

    var datasetModeEl = document.getElementById("dataset-auto-approve-mode");
    var modelModeEl = document.getElementById("model-auto-approve-mode");
    if (datasetModeEl) {
        datasetModeEl.addEventListener("change", function () {
            var container = document.getElementById("dataset-allow-list-container");
            if (container) container.classList.toggle("hidden", this.value !== "ALLOWLIST");
        });
    }
    if (modelModeEl) {
        modelModeEl.addEventListener("change", function () {
            var container = document.getElementById("model-allow-list-container");
            if (container) container.classList.toggle("hidden", this.value !== "ALLOWLIST");
        });
    }

    parseEmails(document.getElementById("model-allow-list-emails"));
    parseEmails(document.getElementById("dataset-allow-list-emails"));
    parseEmails(document.getElementById("committee-members-emails"));

    bindEmailInputs();

    var savePolicyBtn = document.getElementById("save-policy-btn");
    if (savePolicyBtn) savePolicyBtn.addEventListener("click", function (e) {
        var message = buildAssociationsPolicyConfirmMessage("update benchmark associations policy?");
        if (message !== null) showConfirmModal(e.currentTarget, updateAssociationsPolicy, message);
    });

    var saveCommitteeBtn = document.getElementById("save-committee-members-btn");
    if (saveCommitteeBtn) saveCommitteeBtn.addEventListener("click", function (e) {
        var message = buildCommitteeMembersConfirmMessage("update benchmark committee members?");
        if (message !== null) showConfirmModal(e.currentTarget, updateCommitteeMembers, message);
    });

    if (datasetModeEl) datasetModeEl.dispatchEvent(new Event("change"));
    if (modelModeEl) modelModeEl.dispatchEvent(new Event("change"));

    var dashBtn = document.getElementById("dashboard-btn");
    var dashFormWrap = document.getElementById("dashboard-form-wrapper");
    var redirectForm = document.getElementById("redirect-dashobard-form");
    if (dashBtn && dashFormWrap) {
        dashBtn.addEventListener("click", function () {
            var open = !dashFormWrap.classList.contains("hidden");
            dashFormWrap.classList.toggle("hidden", open);
            var icon = dashBtn.querySelector("i");
            if (icon) icon.style.transform = open ? "rotate(0deg)" : "rotate(180deg)";
        });
    }
    if (redirectForm) {
        redirectForm.addEventListener("submit", function (e) {
            e.preventDefault();
            var stagesEl = document.getElementById("stages-path");
            var instEl = document.getElementById("institutions-path");
            if (!stagesEl || !(stagesEl.value || "").trim()) {
                showErrorToast("Make sure to enter a valid path for the stages file");
                return;
            }
            if (!instEl || !(instEl.value || "").trim()) {
                showErrorToast("Make sure to enter a valid path for the institutions file");
                return;
            }
            redirectForm.submit();
        });
    }
    var browseStages = document.getElementById("browse-stages-btn");
    if (browseStages) browseStages.addEventListener("click", function () {
        browseWithFiles = true;
        browseFolderHandler("stages-path");
    });
    var browseInst = document.getElementById("browse-institutions-btn");
    if (browseInst) browseInst.addEventListener("click", function () {
        browseWithFiles = true;
        browseFolderHandler("institutions-path");
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBenchmarkDetail);
} else {
    initBenchmarkDetail();
}
