function onDatasetRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Dataset Registered Successfully");
        timer(3, "/datasets/ui/display/"+response.dataset_id);
    }
    else{
        showErrorModal("Failed to Register Dataset", response)
    }
}

async function registerDataset(registerButton){
    addSpinner(registerButton);
    
    const formData = new FormData($("#dataset-register-form")[0]);

    disableElements("#dataset-register-form input, #dataset-register-form select, #dataset-register-form textarea, #dataset-register-form button");

    ajaxRequest(
        "/datasets/register",
        "POST",
        formData,
        onDatasetRegisterSuccess,
        "Error registering dataset:"
    );

    window.runningTaskId = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkDatasetFormValidity() {
    const isValid = Boolean(
        $("#benchmark").val() &&
        $("#name").val().trim() &&
        $("#description").val().trim() &&
        $("#location").val().trim() &&
        $("#data-path").val().trim() &&
        $("#labels-path").val().trim()
    );
    $("#register-dataset-btn").prop("disabled", !isValid);
}

function loadFolder(path) {
    fetch(`/api/browse?path=${encodeURIComponent(path)}`)
        .then(response => response.json())
        .then(data => {
            const folderList = document.getElementById("folder-list");
            folderList.innerHTML = "";
            if (data.parent) {
                folderList.innerHTML += `<li class='list-group-item folder-item' data-path='${data.parent}'>.. (parent)</li>`;
            }
            data.folders.forEach(folder => {
                folderList.innerHTML += `<li class='list-group-item folder-item' data-path='${folder.path}'>${folder.name}</li>`;
            });
        });
}

$(document).ready(() => {
    $("#register-dataset-btn").on("click", (e) => {
        registerDataset(e.currentTarget);
    });
    $("#dataset-register-form input, #dataset-register-form select, #dataset-register-form textarea").on("change keyup", checkDatasetFormValidity);
});

// AJAX folder browsing logic
let currentPath = ".";  // Start at root directory or a defined base path
let activeInput = null;

$("#browse-data-btn").on("click", () => {
    activeInput = document.getElementById("data-path");
    loadFolder(currentPath);
    $("#folder-picker-modal-title").html("Select Folder");
    $("#folder-picker-modal").modal("show");
});

$("#browse-labels-btn").on("click", () => {
    activeInput = document.getElementById("labels-path");
    loadFolder(currentPath);
    $("#folder-picker-modal-title").html("Select Folder");
    $("#folder-picker-modal").modal("show");
});

$("#folder-list").on("click", (e) => {
    if (e.target.classList.contains("folder-item")) {
        const newPath = e.target.getAttribute("data-path");
        currentPath = newPath;
        loadFolder(newPath);
    }
});

$("#select-folder-btn").on("click", () => {
    if (activeInput) {
        activeInput.value = currentPath;
        $(activeInput).trigger("keyup");
    }
    $("#folder-picker-modal").modal("hide");
});