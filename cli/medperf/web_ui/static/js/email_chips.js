/**
 * Email chips inputs.
 *
 * Used by the allow lists (benchmark associations policy, committee members,
 * container access). An email typed in an `.email-input` becomes a removable
 * "chip" when the user hits Enter, comma or space (or pastes a list of emails).
 * The chips are inserted before the input, inside its container, which is the
 * element passed to getEmailsList/setEmailChips/parseEmails.
 *
 * Depends on notifications.js (showToast).
 */

/** Loose email format check. */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/** Show a validation error to the user. */
function showErrorToast(message) {
    showToast("Validation Error", message, "danger");
}

/**
 * Return the emails of the chips inside a container.
 */
function getEmailsList(container) {
    if (!container) return [];
    return Array.prototype.map.call(container.querySelectorAll(".email-chip"), function (chip) {
        return chip.getAttribute("data-email");
    });
}

/**
 * Add a chip for an email before the given input (ignored if the email is
 * already in the list, case-insensitively).
 */
function createEmailChip(email, inputElement) {
    if (!inputElement || !inputElement.parentNode) return;
    var normalizedEmail = email.toLowerCase();
    var alreadyAdded = getEmailsList(inputElement.parentNode).some(function (existing) {
        return existing.toLowerCase() === normalizedEmail;
    });
    if (alreadyAdded) return;

    var chip = document.createElement("div");
    chip.className = "email-chip inline-block bg-muted-strong rounded-full py-1 px-3 mr-2 mb-2 text-sm";
    chip.setAttribute("data-email", email);
    chip.textContent = email;
    var remove = document.createElement("span");
    remove.className = "remove-btn ml-2 cursor-pointer font-bold";
    remove.textContent = "×";
    remove.setAttribute("aria-label", "Remove " + email);
    remove.addEventListener("click", function () { chip.remove(); });
    chip.appendChild(remove);
    inputElement.parentNode.insertBefore(chip, inputElement);
}

/** Remove all the chips of a container. */
function clearEmailChips(container) {
    if (!container) return;
    container.querySelectorAll(".email-chip").forEach(function (chip) { chip.remove(); });
}

/**
 * Replace the chips of a container with the given emails.
 */
function setEmailChips(container, emails) {
    clearEmailChips(container);
    var inputEl = container ? container.querySelector("input") : null;
    (emails || []).forEach(function (email) {
        email = (email || "").trim();
        if (email) createEmailChip(email, inputEl);
    });
}

/**
 * Create the chips of the emails saved in the container's `data-allowed-list`
 * attribute (a JSON list), e.g. the current allow list rendered by the server.
 */
function parseEmails(container) {
    if (!container || !container.getAttribute) return;
    var emails = [];
    try { emails = JSON.parse(container.getAttribute("data-allowed-list") || "[]"); } catch (_) {}
    // Anything but a list (e.g. "{}") means no emails: it must not break the page
    setEmailChips(container, Array.isArray(emails) ? emails : []);
}

/**
 * Turn every `.email-input` into an email chips input: typed or pasted
 * emails become chips; invalid ones are ignored.
 */
function bindEmailInputs() {
    document.querySelectorAll(".email-input").forEach(function (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " " || e.key === ",") {
                e.preventDefault();
                var email = input.value.trim().replace(/,$/, "");
                if (email && isValidEmail(email)) {
                    createEmailChip(email, input);
                    input.value = "";
                }
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
}
