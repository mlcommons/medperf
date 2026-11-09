/*
 * Aggregator details page: getting its server certificate, running it for a
 * training experiment, and showing/stopping the running aggregator container.
 */

var REDIRECT_BASE = "/aggregators/ui/display/";

// Name of the aggregator container task on the server (see /api/running_tasks)
var AGGREGATOR_CONTAINER_TASK_NAME = "start_aggregator";

/** Show the "aggregator is running" banner (and dim the run card) while it runs. */
function updateRunningBanner(isRunning) {
    var banner = document.getElementById("aggregator-running-banner");
    var runCard = document.getElementById("aggregator-run-card");
    if (!banner || !runCard) return;
    banner.classList.toggle("hidden", !isRunning);
    runCard.classList.toggle("opacity-80", isRunning);
}

/** Poll whether the aggregator container is running (after running it). */
function startPollingRunningTasks() {
    watchRunningContainer(AGGREGATOR_CONTAINER_TASK_NAME, updateRunningBanner);
}

/** Handle the response of getting the server certificate. */
function onGetServerCertSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Server Certificate Retrieved Successfully", seconds: 3 });
    } else {
        showErrorModal("Failed to Get Server Certificate", response);
    }
}

/** Handle the response of running the aggregator. */
function onRunAggregatorSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Aggregator Ran Successfully", seconds: 3 });
    } else showErrorModal("Something went wrong while running the aggregator", response);
}

/** Stop the running aggregator container. */
function stopAggregator() {
    stopRunningContainer(AGGREGATOR_CONTAINER_TASK_NAME, document.getElementById("stop-aggregator-btn"), function () {
        updateRunningBanner(false);
        displayAlert("success", "Aggregator stopped.");
    });
}

/** Bind the page forms and buttons. */
function init() {
    var actionForms = document.querySelectorAll('#start-aggregator-form, #get-server-cert-form');
    actionForms.forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });

    var stopBtn = document.getElementById("stop-aggregator-btn");
    if (stopBtn) stopBtn.addEventListener("click", function (e) {
        showConfirmModal(e.currentTarget, function () { stopAggregator(); }, "stop the running aggregator?");
    });

}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}