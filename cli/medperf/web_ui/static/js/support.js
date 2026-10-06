/**
 * "Get support" window.
 *
 * Shows the latest web UI log lines and helps the user send them to the
 * MedPerf team: as an email draft opened in their mail client (mailto links
 * can't carry attachments, so the draft only contains the latest lines), and
 * as the full logs package they can download and attach themselves.
 * Nothing is sent automatically.
 */

var SUPPORT_EMAIL_LOG_LINES = 30; // Log lines included in the email draft
var SUPPORT_EMAIL_MAX_LINE_CHARS = 300; // Longer log lines are shortened in the email draft
var SUPPORT_EMAIL_MAX_ENCODED_BODY = 1800; // Some mail clients cut mailto links longer than ~2000 chars
var SUPPORT_EMAIL_SUBJECT = "MedPerf web UI support request";

/**
 * Build the email body: the user's description, environment details and as
 * many of the latest log lines as fit in the (URL-encoded) size limit,
 * keeping the newest lines.
 */
function buildSupportEmailBody(info, description) {
    var header = "Hello MedPerf team,\n\n";
    header += (description || "[Please describe the problem here]") + "\n\n";
    header += "Environment:\n";
    Object.keys(info.environment || {}).forEach(function (key) {
        header += "- " + key + ": " + info.environment[key] + "\n";
    });
    var footer = "\n(Please attach the logs file downloaded from the web UI: medperf_logs.tar.gz)\n";

    var lines = (info.log_lines || []).slice(-SUPPORT_EMAIL_LOG_LINES).map(function (line) {
        return line.length > SUPPORT_EMAIL_MAX_LINE_CHARS ? line.slice(0, SUPPORT_EMAIL_MAX_LINE_CHARS) + "..." : line;
    });
    function compose() {
        var logsSection = lines.length ? "\nLatest web UI log lines:\n" + lines.join("\n") + "\n" : "";
        return header + logsSection + footer;
    }
    var body = compose();
    while (lines.length && encodeURIComponent(body).length > SUPPORT_EMAIL_MAX_ENCODED_BODY) {
        lines.shift();
        body = compose();
    }
    return body;
}

function buildSupportMailto(info, description) {
    // Each address is encoded separately: the commas separating them (and the @) must stay literal
    var to = (info.emails || []).map(function (email) { return encodeURIComponent(email).replace(/%40/g, "@"); }).join(",");
    return "mailto:" + to +
        "?subject=" + encodeURIComponent(SUPPORT_EMAIL_SUBJECT) +
        "&body=" + encodeURIComponent(buildSupportEmailBody(info, description));
}

function showSupportModal(info) {
    var logText = (info.log_lines || []).join("\n") || "No web UI logs were found.";
    var recipients = info.emails || [];
    var recipientNote = recipients.length
        ? "The draft will be addressed to <strong>" + escapeHtml(recipients.join(", ")) + "</strong>."
        : "No support email is configured: enter the recipient in the draft.";

    var body = "";
    body += "<p class=\"mb-3\">Describe the problem, then open an email draft in your mail client. Nothing is sent until you send it yourself. " + recipientNote + "</p>";
    body += "<label for=\"support-description\" class=\"block text-secondary font-semibold mb-2\">What went wrong?</label>";
    body += "<textarea id=\"support-description\" rows=\"3\" class=\"w-full px-4 py-3 rounded-xl border-2 border-border-strong dark:border-border dark:bg-card-muted dark:text-ink focus:outline-none focus:border-brand-accent\" placeholder=\"e.g. Dataset preparation fails after the sanity check\"></textarea>";
    body += "<p class=\"text-sm text-secondary font-semibold mt-4 mb-2\">Latest web UI log lines <span class=\"font-normal text-muted-fg break-all\">(" + escapeHtml(info.log_file || "") + ")</span></p>";
    // column-reverse keeps the box scrolled to the bottom, so the newest lines show first
    body += "<div style=\"max-height: 18rem; overflow: auto; display: flex; flex-direction: column-reverse\" class=\"rounded-lg bg-muted\">";
    body += "<pre id=\"support-log\" class=\"p-3 text-xs whitespace-pre-wrap break-words\">" + escapeHtml(logText) + "</pre></div>";
    body += "<p class=\"text-xs text-muted-fg mt-2\">Email drafts can't carry attachments, so the draft only includes the last lines. Download the full logs and attach the file to your email.</p>";

    var footer = "";
    footer += "<button type=\"button\" class=\"btn btn-sm btn-secondary close-modal-btn\">Close</button>";
    footer += "<button type=\"button\" id=\"support-copy-btn\" class=\"btn btn-sm btn-secondary\"><i class=\"fas fa-copy mr-1\" aria-hidden=\"true\"></i>Copy logs</button>";
    footer += "<a href=\"/api/support/logs\" download class=\"btn btn-sm btn-secondary\"><i class=\"fas fa-download mr-1\" aria-hidden=\"true\"></i>Download full logs</a>";
    footer += "<button type=\"button\" id=\"support-email-btn\" class=\"btn btn-sm btn-primary\"><i class=\"fas fa-envelope mr-1\" aria-hidden=\"true\"></i>Open email draft</button>";

    showModal({
        title: "Get support",
        body: body,
        footer: footer,
        modalClasses: "max-w-3xl w-full",
        extra_func: function () {
            document.getElementById("support-email-btn").addEventListener("click", function () {
                var description = document.getElementById("support-description").value.trim();
                window.open(buildSupportMailto(info, description), "_blank");
            });
            document.getElementById("support-copy-btn").addEventListener("click", function () {
                navigator.clipboard.writeText(logText).then(
                    function () { displayAlert("success", "Logs copied to the clipboard"); },
                    function () { displayAlert("danger", "Could not copy the logs"); }
                );
            });
        },
    });
}

/**
 * Fetch the support information from the server and open the support window.
 */
function openSupport() {
    fetch("/api/support/info")
        .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
        })
        .then(showSupportModal)
        .catch(function (err) {
            displayAlert("danger", "Could not load the support information: " + err.message);
        });
}

(function bindSupportButton() {
    function bind() {
        var btn = document.getElementById("support-btn");
        if (btn) btn.addEventListener("click", openSupport);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
    else bind();
})();
