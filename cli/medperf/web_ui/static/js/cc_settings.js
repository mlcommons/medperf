// One confidential-computing settings form per role. Operating a workload and
// receiving its results are separate roles, so each gets its own form, and
// everything here is found by section rather than by fixed element ids: a new
// role needs an entry in `cc_sections` server-side and nothing in this file.

function ccSectionPreferences(section) {
    var all = window.ccPreferences || {};
    return all[section] || {};
}

function ccFieldInputs(section) {
    // Only the chosen backend's fields. Every backend's fields are rendered
    // and all but one are hidden, so taking the whole container would judge
    // the form on settings belonging to a provider nobody selected -- leaving
    // the apply button disabled until every backend was filled in.
    var container = document.getElementById("edit-cc-" + section + "-fields");
    if (!container) return [];
    var select = container.querySelector(".cc-backend-select");
    var backend = select ? select.value : "";
    if (!backend) return [];
    var group = container.querySelector(
        ".cc-backend-fields[data-backend='" + backend + "']"
    );
    if (!group) return [];
    return Array.prototype.slice.call(group.querySelectorAll("input[type='text']"));
}

function ccFieldKey(input) {
    // The backend field selector names inputs "<section>-<setting>".
    var name = input.id || "";
    var dash = name.indexOf("-");
    return dash === -1 ? name : name.slice(dash + 1);
}

function onCCSettingsEditRequestSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({
            title: "CC Configuration Edited Successfully",
            seconds: 3,
        });
    } else {
        showErrorModal("Failed to Edit CC Configuration", response);
    }
}

function checkForCCChanges(section) {
    var preferences = ccSectionPreferences(section);
    var defaults = preferences.defaults || {};
    var configureEl = document.getElementById("configure-cc-" + section);
    var configureChecked = configureEl ? configureEl.checked : false;
    if (configureChecked !== Boolean(preferences.configured)) {
        return true;
    }
    if (!configureChecked) {
        // Turned on, filled in, then turned off again is no change.
        return false;
    }
    var inputs = ccFieldInputs(section);
    for (var i = 0; i < inputs.length; i++) {
        var defaultValue = defaults[ccFieldKey(inputs[i])];
        if ((inputs[i].value || "") !== (defaultValue === undefined ? "" : defaultValue)) {
            return true;
        }
    }
    return false;
}

function checkCCFormValidity(section) {
    var configureEl = document.getElementById("configure-cc-" + section);
    if (!configureEl || !configureEl.checked) {
        return true; // Nothing to validate when the section is turned off.
    }
    var inputs = ccFieldInputs(section);
    for (var i = 0; i < inputs.length; i++) {
        if ((inputs[i].value || "").trim().length === 0) {
            return false;
        }
    }
    return true;
}

function checkCanApplyChanges(section) {
    var preferences = ccSectionPreferences(section);
    var canApplyWithoutChanges = !preferences.initialized && preferences.configured;
    var applyBtn = document.getElementById("apply-cc-" + section + "-btn");
    if (!applyBtn) return;

    if (!checkForCCChanges(section)) {
        applyBtn.disabled = !canApplyWithoutChanges;
    } else {
        applyBtn.disabled = !checkCCFormValidity(section);
    }
}

function initCCSection(container) {
    var section = container.getAttribute("data-cc-section");
    var form = document.getElementById("edit-cc-" + section + "-form");
    if (!form) return;
    form.addEventListener("submit", submitActionForm);

    var configureEl = document.getElementById("configure-cc-" + section);
    var fieldsContainer = document.getElementById("edit-cc-" + section + "-fields");
    if (configureEl && fieldsContainer) {
        var toggleFields = function () {
            fieldsContainer.style.display = configureEl.checked ? "" : "none";
            if (!configureEl.checked) fieldsContainer.classList.add("hidden");
            else fieldsContainer.classList.remove("hidden");
        };
        configureEl.addEventListener("change", toggleFields);
        toggleFields();
    }

    var watched = form.querySelectorAll("input[type='text'], input[type='checkbox']");
    var onChange = function () { checkCanApplyChanges(section); };
    for (var i = 0; i < watched.length; i++) {
        watched[i].addEventListener("keyup", onChange);
        watched[i].addEventListener("change", onChange);
    }
    checkCanApplyChanges(section);
}

function initCCSections() {
    var containers = document.querySelectorAll("[data-cc-section]");
    for (var i = 0; i < containers.length; i++) {
        initCCSection(containers[i]);
    }
}

if (typeof window !== "undefined") {
    window.onCCSettingsEditRequestSuccess = onCCSettingsEditRequestSuccess;
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCCSections);
else initCCSections();
