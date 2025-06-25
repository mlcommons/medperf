function loadFolder(path) {
    $.ajax({
        url: "/api/browse",
        method: "POST",
        data: { path: path, with_files: browseWithFiles},
        success: function(response) {
            currentPath = response.current_folder;
            const folderList = $("#folder-list");
            folderList.empty();

            if (response.parent) {
                if(response.have_parent)
                    folderList.append(`<li class='list-group-item folder-item' data-path='${response.parent}'>.. (parent)</li>`);
                else
                    folderList.append(`<li class='list-group-item folder-item parent-disabled' data-path='${response.parent}'>.. (parent)</li>`);
            }

            response.folders.forEach(item => {
                if (item.type === "dir")
                    folderList.append(`<li class='list-group-item folder-item' data-path='${item.path}'>${item.name}</li>`);
                else
                    folderList.append(`<li class='list-group-item folder-item file-item' data-path='${item.path}'>${item.name}</li>`);
            });
            $("#folder-picker-modal-title").html(`Select Path: <code>${currentPath}</code>`);
        }
    });
}

function browseFolderHandler(elementId){
    activeInput = document.getElementById(elementId);
    if (currentPathType === "file"){
        currentPathType = "folder";
        currentPath += "/..";
    }
    loadFolder(currentPath);
    $("#folder-picker-modal").modal("show");
}

// AJAX folder browsing logic
let currentPath = ".";
let currentPathType = "folder";
let browseWithFiles = false;
let activeInput = null;

$(document).ready(() => {
    $("#folder-list").on("click", (e) => {
        const clickedElement = e.target;
        if (clickedElement.classList.contains("file-item")){
            currentPath = e.target.getAttribute("data-path");
            $("#folder-picker-modal-title").html(`<b>Selected File:</b> <code>${currentPath}</code>`);
            currentPathType = "file";
        }
        else if (
            clickedElement.classList.contains("folder-item") &&
            !clickedElement.classList.contains("parent-disabled")
        ) {
            currentPath = e.target.getAttribute("data-path");
            if (currentPathType === "file"){
                currentPathType = "folder";
                currentPath += "/..";
            }
            loadFolder(currentPath);
        }
    });
    
    $("#select-folder-btn").on("click", () => {
        if (activeInput) {
            activeInput.value = currentPath;
            $(activeInput).trigger("keyup");
        }
        $("#folder-picker-modal").modal("hide");
    });
});