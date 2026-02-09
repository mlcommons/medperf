function onContainerAssociationRequestSuccess(response) {
    markAllStagesAsComplete();
    if (response && response.status === "success") {
        showReloadModal({ title: "Association Requested Successfully", seconds: 3 });
    } else {
        showErrorModal("Association Request Failed", response);
    }
}

function requestContainerAssociation(requestAssociationButton) {
    var dropdownDiv = document.getElementById("dropdown-div");
    if (dropdownDiv) { dropdownDiv.classList.remove("show"); dropdownDiv.style.display = "none"; }
    var associateBtn = document.getElementById("associate-dropdown-btn");
    if (associateBtn) addSpinner(associateBtn);
    var containerId = requestAssociationButton.getAttribute("data-container-id");
    var benchmarkId = requestAssociationButton.getAttribute("data-benchmark-id");
    var formData = new FormData();
    formData.append("container_id", containerId);
    formData.append("benchmark_id", benchmarkId);
    disableElements(".card button");
    ajaxRequest("/containers/associate", "POST", formData, onContainerAssociationRequestSuccess, "Error requesting container association:");
    showPanel("Requesting Container Association...");
    getTaskId().then(function (id) { window.runningTaskId = id; });
    if (typeof streamEvents === "function") streamEvents(logPanel, stagesList, currentStageElement);
}

function init() {
    document.querySelectorAll(".request-association-btn").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            showConfirmModal(e.currentTarget, requestContainerAssociation, "request container association?");
        });
    });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
