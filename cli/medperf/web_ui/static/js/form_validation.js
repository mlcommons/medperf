/**
 * Form validation feedback.
 *
 * Forms keep their submit button disabled while their inputs are invalid.
 * This module also tells the user why:
 *  - a checklist under the submit button lists what is still missing or invalid,
 *  - each invalid field gets a red border and a message below it, but only once
 *    the user has interacted with it (so a fresh form isn't covered in errors),
 *  - the disabled button's tooltip lists the reasons too.
 *
 * Usage, in a form's validity check:
 *     var problems = [];
 *     if (!nameEl.value.trim()) problems.push({ field: nameEl, message: "Enter a name" });
 *     submitBtn.disabled = !showFormProblems(submitBtn, problems);
 *
 * `field` is optional (e.g. for a choice between radio buttons): such problems
 * only appear in the checklist.
 */

// Last problems reported for each submit button (by button id), so the feedback
// can be refreshed when a field is touched without re-running the validity check.
var formProblemsByButton = {};
// Fields currently shown as invalid for each submit button (by button id)
var invalidFieldsByButton = {};

/**
 * Return the element the user sees for a field. Searchable selects keep their
 * value in a hidden input, so their visible search box is returned instead.
 */
function getVisibleField(field) {
    if (field.type === "hidden") {
        var searchable = field.closest(".searchable-select");
        var query = searchable && searchable.querySelector(".searchable-select-query");
        if (query) return query;
    }
    return field;
}

/**
 * Return the element after which a field's error message is inserted: the row
 * directly holding the field and its buttons/tooltip, or the field itself.
 */
function getFieldRow(field) {
    var el = field.closest(".searchable-select") || field;
    var parent = el.parentElement;
    return parent && parent.classList.contains("flex") ? parent : el;
}

function getFieldErrorId(field) {
    return (field.id || field.name) + "-error";
}

/**
 * Remember when the user has interacted with a field, and refresh the feedback
 * then (e.g. leaving a required field empty shows its error right away).
 */
function trackFieldTouched(field, submitBtn) {
    var visible = getVisibleField(field);
    if (visible.dataset.validationTracked) return;
    visible.dataset.validationTracked = "true";
    var markTouched = function () {
        visible.dataset.touched = "true";
        renderFormProblems(submitBtn, formProblemsByButton[submitBtn.id] || []);
    };
    visible.addEventListener("blur", markTouched);
    visible.addEventListener("change", markTouched);
}

function clearFieldError(field) {
    var visible = getVisibleField(field);
    visible.classList.remove("field-invalid");
    visible.removeAttribute("aria-invalid");
    var message = document.getElementById(getFieldErrorId(field));
    if (message) message.remove();
}

function showFieldError(field, text) {
    var visible = getVisibleField(field);
    visible.classList.add("field-invalid");
    visible.setAttribute("aria-invalid", "true");
    var id = getFieldErrorId(field);
    var message = document.getElementById(id);
    if (!message) {
        message = document.createElement("p");
        message.id = id;
        message.className = "field-error-message";
        getFieldRow(field).insertAdjacentElement("afterend", message);
        visible.setAttribute("aria-describedby", id);
    }
    message.textContent = text;
}

/**
 * Show (or hide, if there are no problems) the checklist under the submit button.
 */
function renderProblemsChecklist(submitBtn, problems) {
    var id = submitBtn.id + "-problems";
    var checklist = document.getElementById(id);
    if (!problems.length) {
        if (checklist) checklist.remove();
        return;
    }
    if (!checklist) {
        checklist = document.createElement("div");
        checklist.id = id;
        checklist.className = "form-problems";
        checklist.setAttribute("role", "status");
        checklist.setAttribute("aria-live", "polite");
        // Place it after the button's container (e.g. the centered buttons row)
        var anchor = submitBtn.parentElement && submitBtn.parentElement.tagName !== "FORM" ? submitBtn.parentElement : submitBtn;
        anchor.insertAdjacentElement("afterend", checklist);
    }
    var items = problems.map(function (p) { return "<li>" + escapeHtml(p.message) + "</li>"; }).join("");
    checklist.innerHTML = "<p class=\"form-problems-title\">To continue, please:</p><ul>" + items + "</ul>";
}

function renderFormProblems(submitBtn, problems) {
    // Fields of other forms are disabled (and may be empty) while a task runs
    if (window.taskRunning) problems = [];

    renderProblemsChecklist(submitBtn, problems);
    submitBtn.title = problems.length ? "To continue, please:\n- " + problems.map(function (p) { return p.message; }).join("\n- ") : "";

    var problemFields = [];
    problems.forEach(function (p) {
        if (!p.field) return;
        trackFieldTouched(p.field, submitBtn);
        problemFields.push(p.field);
        if (getVisibleField(p.field).dataset.touched) showFieldError(p.field, p.message);
        else clearFieldError(p.field);
    });
    // Clear the errors of fields that became valid
    (invalidFieldsByButton[submitBtn.id] || []).forEach(function (field) {
        if (problemFields.indexOf(field) === -1) clearFieldError(field);
    });
    invalidFieldsByButton[submitBtn.id] = problemFields;
}

/**
 * Show why a form can't be submitted yet.
 *
 * @param {HTMLElement} submitBtn - the form's submit button (must have an id).
 * @param {Array<{field: (HTMLElement|null), message: string}>} problems - what is missing or invalid.
 * @returns {boolean} true if there are no problems.
 */
function showFormProblems(submitBtn, problems) {
    if (!submitBtn) return problems.length === 0;
    formProblemsByButton[submitBtn.id] = problems;
    renderFormProblems(submitBtn, problems);
    return problems.length === 0;
}

/**
 * Add a problem to `problems` if the given text input is empty.
 */
function requireValue(problems, field, message) {
    if (field && !field.value.trim()) problems.push({ field: field, message: message });
}
