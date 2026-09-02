(function () {
    "use strict";

    const DISMISS_KEY = "medperf-update-banner-dismissed";
    const UPDATE_KEY = "medperf-update-in-progress";
    const POLL_MS = 1500;
    const TIMEOUT_MS = 5 * 60 * 1000;

    function fetchJson(url, options) {
        return fetch(url, options)
            .then(function (response) {
                return response.json().then(function (body) {
                    return { ok: response.ok, body: body };
                });
            })
            .catch(function () {
                return { ok: false, body: {} };
            });
    }

    function showOverlay(message, failed) {
        var overlay = document.getElementById("client-update-overlay");
        if (!overlay) return;

        overlay.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");

        var title = document.getElementById("client-update-overlay-title");
        var msg = document.getElementById("client-update-overlay-message");
        var icon = document.getElementById("client-update-overlay-icon");
        var dismiss = document.getElementById("client-update-overlay-dismiss");

        if (title) title.textContent = failed ? "Update failed" : "Updating MedPerf";
        if (msg) msg.textContent = message;
        if (icon) {
            icon.className = failed
                ? "fas fa-exclamation-triangle text-2xl text-amber-600"
                : "fas fa-sync-alt fa-spin text-2xl";
        }
        if (dismiss) dismiss.classList.toggle("hidden", !failed);
    }

    function hideOverlay() {
        var overlay = document.getElementById("client-update-overlay");
        if (!overlay) return;
        overlay.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
    }

    function showProgressBanner(targetVersion) {
        var progress = document.getElementById("client-update-progress-banner");
        var banner = document.getElementById("client-update-banner");
        if (banner) banner.classList.add("hidden");
        if (!progress) return;

        var label = document.getElementById("client-update-progress-label");
        if (label) {
            label.textContent = targetVersion
                ? "Updating MedPerf to " + targetVersion + "…"
                : "MedPerf update in progress…";
        }
        progress.classList.remove("hidden");
    }

    function saveUpdateSession(targetVersion) {
        try {
            sessionStorage.setItem(
                UPDATE_KEY,
                JSON.stringify({ targetVersion: targetVersion, startedAt: Date.now() })
            );
        } catch (_) {}
    }

    function loadUpdateSession() {
        try {
            var raw = sessionStorage.getItem(UPDATE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) {
            return null;
        }
    }

    function clearUpdateSession() {
        try {
            sessionStorage.removeItem(UPDATE_KEY);
        } catch (_) {}
    }

    function setInstructionsExpanded(expanded) {
        var panel = document.getElementById("client-update-instructions");
        var button = document.getElementById("client-update-instructions-btn");
        var label = document.getElementById("client-update-instructions-label");
        var chevron = document.getElementById("client-update-instructions-chevron");
        if (!panel || !button) return;

        panel.classList.toggle("hidden", !expanded);
        panel.setAttribute("aria-hidden", expanded ? "false" : "true");
        button.setAttribute("aria-expanded", expanded ? "true" : "false");
        if (label) label.textContent = expanded ? "Hide update steps" : "Show update steps";
        if (chevron) chevron.classList.toggle("rotate-180", expanded);
    }

    function showBanner(info, ignoreDismiss) {
        var banner = document.getElementById("client-update-banner");
        if (!banner || !info) return;

        window.updateCheck = info;
        setInstructionsExpanded(false);

        var latest = info.latest_version || "";
        var current = info.current_version || "";
        var show = Boolean(info.update_available && latest);

        if (show && !ignoreDismiss) {
            try {
                if (localStorage.getItem(DISMISS_KEY) === latest) show = false;
            } catch (_) {}
        }

        if (!show) {
            banner.classList.add("hidden");
            return;
        }

        var isEditable = Boolean(info.is_editable_install);

        var summary = document.getElementById("client-update-summary");
        if (summary) {
            summary.textContent = "A new MedPerf release is available: ";

            var latestEl = document.createElement("strong");
            latestEl.className = "font-semibold text-amber-800 dark:text-amber-200";
            latestEl.textContent = latest;
            summary.appendChild(latestEl);

            var currentEl = document.createElement("span");
            currentEl.className = "text-gray-600 dark:text-gray-300";
            currentEl.textContent = " (you have " + current + ")";
            summary.appendChild(currentEl);

            if (isEditable) {
                var editableEl = document.createElement("span");
                editableEl.className = "block text-xs text-gray-600 dark:text-gray-300 mt-0.5";
                editableEl.textContent =
                    "This is an editable (development) install - update it with git pull, not the button below.";
                summary.appendChild(editableEl);
            }
        }

        var command = document.getElementById("client-update-command");
        if (command) command.textContent = info.update_command || "pip install -U medperf";

        var updateBtn = document.getElementById("client-update-now-btn");
        if (updateBtn) {
            updateBtn.classList.toggle("hidden", isEditable);
            updateBtn.disabled = Boolean(window.taskRunning);
        }

        banner.dataset.latestVersion = latest;
        banner.dataset.currentVersion = current;
        banner.dataset.isEditableInstall = isEditable ? "true" : "false";
        banner.classList.remove("hidden");
    }

    function checkForUpdates() {
        document.querySelectorAll(".check-for-updates-btn").forEach(function (btn) {
            btn.disabled = true;
        });

        fetchJson("/api/update_check?refresh=true").then(function (result) {
            if (!result.ok) {
                if (typeof showToast === "function") {
                    showToast(
                        "Update check failed",
                        result.body.detail || "Could not check for updates.",
                        "text-bg-danger"
                    );
                }
                return;
            }

            var body = result.body;
            showBanner(body, true);

            if (typeof showToast !== "function") return;

            var toastClass = "text-bg-success";
            if (!body.check_ok) toastClass = "text-bg-danger";
            else if (body.update_available) toastClass = "text-bg-warning";
            showToast("MedPerf updates", body.message, toastClass);
        }).finally(function () {
            document.querySelectorAll(".check-for-updates-btn").forEach(function (btn) {
                btn.disabled = false;
            });
        });
    }

    function failUpdate(message) {
        clearUpdateSession();
        showOverlay(message, true);
        showBanner(window.updateCheck || {}, false);
    }

    function waitForRestart(targetVersion, startedAt) {
        if (Date.now() - startedAt > TIMEOUT_MS) {
            failUpdate("Timed out waiting for the Web UI to restart. Check the terminal logs.");
            return;
        }

        fetchJson("/api/update_status").then(function (result) {
            if (result.ok) {
                var payload = result.body;
                if (payload.status === "update_failed") {
                    failUpdate(payload.error || "The update failed. Check the terminal logs.");
                    return;
                }
                if (!payload.update_in_progress) {
                    clearUpdateSession();
                    window.location.reload();
                    return;
                }
            }

            window.setTimeout(function () {
                waitForRestart(targetVersion, startedAt);
            }, POLL_MS);
        });
    }

    function startUpdate(targetVersion, currentVersion) {
        if (window.taskRunning) {
            showOverlay("A task is currently running. Wait for it to finish before updating.", true);
            return;
        }

        showOverlay("Downloading the latest release and restarting the Web UI. This may take a minute.", false);
        showProgressBanner(targetVersion);
        saveUpdateSession(targetVersion);

        fetchJson("/api/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                latest_version: targetVersion,
                current_version: currentVersion,
            }),
        }).then(function (result) {
            if (!result.ok) {
                failUpdate(result.body.detail || "Could not start the update.");
                return;
            }
            waitForRestart(targetVersion, Date.now());
        });
    }

    function resumeUpdateIfNeeded() {
        var session = loadUpdateSession();
        if (!session || !session.targetVersion) return false;

        showProgressBanner(session.targetVersion);
        showOverlay(
            "Update in progress. Downloading and restarting the Web UI. This page will reload automatically.",
            false
        );
        waitForRestart(session.targetVersion, session.startedAt || Date.now());
        return true;
    }

    function copyText(elementId, button) {
        var element = document.getElementById(elementId);
        if (!element || !navigator.clipboard) return;
        navigator.clipboard.writeText(element.textContent || "").then(function () {
            if (!button) return;
            var original = button.textContent;
            button.textContent = "Copied";
            window.setTimeout(function () {
                button.textContent = original;
            }, 1500);
        });
    }

    function bindEvents() {
        var banner = document.getElementById("client-update-banner");
        if (!banner || banner.dataset.bound === "true") return;
        banner.dataset.bound = "true";

        var restartCommand = document.getElementById("client-update-restart-command");
        if (restartCommand && window.location.port) {
            restartCommand.textContent = "medperf_webui --port " + window.location.port;
        }

        var updateBtn = document.getElementById("client-update-now-btn");
        if (updateBtn) {
            updateBtn.addEventListener("click", function (e) {
                if (updateBtn.disabled || banner.dataset.isEditableInstall === "true") return;
                var latest = banner.dataset.latestVersion;
                if (!latest) return;
                var currentVersion = banner.dataset.currentVersion || "";
                showConfirmModal(e.currentTarget, function () {
                    startUpdate(latest, currentVersion);
                }, "update MedPerf to " + latest + " now?");
            });
        }

        var instructionsBtn = document.getElementById("client-update-instructions-btn");
        if (instructionsBtn) {
            instructionsBtn.addEventListener("click", function () {
                var panel = document.getElementById("client-update-instructions");
                setInstructionsExpanded(panel && panel.classList.contains("hidden"));
            });
        }

        var dismissBtn = document.getElementById("client-update-dismiss-btn");
        if (dismissBtn) {
            dismissBtn.addEventListener("click", function () {
                if (banner.dataset.latestVersion) {
                    try {
                        localStorage.setItem(DISMISS_KEY, banner.dataset.latestVersion);
                    } catch (_) {}
                }
                banner.classList.add("hidden");
                setInstructionsExpanded(false);
            });
        }

        var overlayDismiss = document.getElementById("client-update-overlay-dismiss");
        if (overlayDismiss) overlayDismiss.addEventListener("click", hideOverlay);

        banner.querySelectorAll(".client-update-copy-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                var targetId = button.getAttribute("data-copy-target");
                if (targetId) copyText(targetId, button);
            });
        });

        document.addEventListener("click", function (event) {
            var button = event.target.closest(".check-for-updates-btn");
            if (!button || button.disabled) return;
            event.preventDefault();
            checkForUpdates();
        });
    }

    function init() {
        bindEvents();
        if (resumeUpdateIfNeeded()) return;
        showBanner(window.updateCheck || {}, false);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
