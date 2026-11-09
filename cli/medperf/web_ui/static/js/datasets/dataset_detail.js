/*
 * Dataset details page: preparation, associations, benchmark executions,
 * results submission and training (with the running training container).
 */

var REDIRECT_BASE = "/datasets/ui/display/";

// Name of the training container task on the server (see /api/running_tasks)
var CONTAINER_TASK_TRAIN = "train";

/** Show the "training is running" banner while the training container runs. */
function updateTrainingRunningBanner(isRunning) {
    var banner = document.getElementById("training-running-banner");
    if (banner) banner.classList.toggle("hidden", !isRunning);
}

/** Poll whether the training container is running (after starting a training). */
function startPollingTrainingRunningTasks() {
    if (!document.getElementById("training-running-banner")) return;
    watchRunningContainer(CONTAINER_TASK_TRAIN, updateTrainingRunningBanner);
}


/** Handle the response of running the training. */
function onRunTrainingSuccess(response) {
    if (response.status === "success") {
        showReloadModal({ title: "Training Ran Successfully", seconds: 3 });
    } else showErrorModal("Something went wrong while running the training", response);
}

/** Stop the running training container. */
function stopTraining() {
    stopRunningContainer(CONTAINER_TASK_TRAIN, document.getElementById("stop-training-btn"), function () {
        updateTrainingRunningBanner(false);
        displayAlert("success", "Training stopped.");
    });
}

/** Bind the page forms and buttons. */
function init() {
    document.querySelectorAll("form[id$='-form']:not(#redirect-export-form), form[id^='dataset-association-form-'], form[id^='dataset-training-association-form-'], form[id^='start-training-form-']").forEach(function (form) {
        form.addEventListener("submit", submitActionForm);
    });
    document.querySelectorAll("[id^='show-']").forEach(function (el) {
        el.addEventListener("click", function () { showResult(el); });
    });
    var exportForm = document.getElementById("redirect-export-form");
    if (exportForm) exportForm.addEventListener("submit", function (e) { e.preventDefault(); });

    var stopTrainingBtn = document.getElementById("stop-training-btn");
    if (stopTrainingBtn) stopTrainingBtn.addEventListener("click", function (e) {
        showConfirmModal(e.currentTarget, function () { stopTraining(); }, "stop the running training?");
    });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();