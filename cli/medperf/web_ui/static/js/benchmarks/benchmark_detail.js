var REDIRECT_BASE = "/benchmarks/ui/display/";

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
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
    var jsonList = [];
    try { jsonList = JSON.parse(raw); } catch (_) {}
    var inputEl = element.querySelector("input");
    for (var i = 0; i < jsonList.length; i++) createEmailChip(jsonList[i], inputEl);
}

function getEmailsList(element) {
    var emailsArr = [];
    if (!element) return emailsArr;
    element.querySelectorAll(".email-chip").forEach(function (chip) {
        var text = (chip.textContent || "").replace(/\s*×\s*$/, "").trim();
        emailsArr.push(text);
    });
    return emailsArr;
}

function showErrorToast(message) {
    showToast("Validation Error", message, "text-bg-danger");
}

function checkUpdateAssociationsPolicyForm() {
    var datasetModeEl = document.getElementById("dataset-auto-approve-mode");
    var modelModeEl = document.getElementById("model-auto-approve-mode");
    var datasetApproveMode = datasetModeEl ? datasetModeEl.value : "NEVER";
    var modelApproveMode = modelModeEl ? modelModeEl.value : "NEVER";
    var isDatasetValid = (datasetApproveMode === "NEVER" || datasetApproveMode === "ALWAYS");
    var isModelValid = (modelApproveMode === "NEVER" || modelApproveMode === "ALWAYS");
    if (!isDatasetValid) {
        var datasetAllowListArr = getEmailsList(document.getElementById("dataset-allow-list-emails"));
        if (datasetAllowListArr.length) isDatasetValid = true;
        else showErrorToast("Make sure that the dataset allow list is not empty");
    }
    if (!isModelValid) {
        var modelAllowListArr = getEmailsList(document.getElementById("model-allow-list-emails"));
        if (modelAllowListArr.length) isModelValid = true;
        else showErrorToast("Make sure that the model allow list is not empty");
    }
    return isDatasetValid && isModelValid;
}

function onUpdateAssociationsPolicySuccess(response) {
    if (response && response.status === "success") {
        showReloadModal({ title: "Benchmark Associations Policy Successfully Updated", seconds: 3 });
    } else {
        showErrorModal("Failed to Update Benchmark Associations Policy", response);
    }
}

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

    document.querySelectorAll(".email-input").forEach(function (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " " || e.key === ",") {
                e.preventDefault();
                var email = this.value.trim().replace(/,$/, "");
                if (email && isValidEmail(email)) {
                    createEmailChip(email, this);
                    this.value = "";
                }
            }
        });
        input.addEventListener("paste", function (e) {
            e.preventDefault();
            var clipboardData = (e.clipboardData || window.clipboardData).getData("text");
            var rawEmails = clipboardData.split(/[\s,]+/);
            rawEmails.forEach(function (email) {
                email = email.trim();
                if (email && isValidEmail(email)) createEmailChip(email, input);
            });
            input.value = "";
        });
    });

    var saveBtn = document.getElementById("save-policy-btn");
    if (saveBtn) saveBtn.addEventListener("click", function (e) {
        if (checkUpdateAssociationsPolicyForm()) showConfirmModal(e.currentTarget, updateAssociationsPolicy, "update benchmark associations policy?");
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
