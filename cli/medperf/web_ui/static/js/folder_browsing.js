function showFolderPickerModal() {
    const el = document.getElementById("folder-picker-modal");
    if (el) { el.classList.remove("hidden"); document.body.classList.add("overflow-hidden"); }
}
function hideFolderPickerModal() {
    const el = document.getElementById("folder-picker-modal");
    if (el) { el.classList.add("hidden"); document.body.classList.remove("overflow-hidden"); }
}

function loadFolder(path) {
    var formData = new FormData();
    formData.append("path", path);
    formData.append("with_files", browseWithFiles);
    fetch("/api/browse", { method: "POST", body: formData })
        .then(function (r) { return r.json(); })
        .then(function (response) {
            currentPath = response.current_folder || "";
            var folderList = document.getElementById("folder-list");
            if (!folderList) return;
            folderList.innerHTML = "";
            if (response.parent) {
                var li = document.createElement("li");
                li.className = response.have_parent ? "folder-item cursor-pointer px-4 py-2 hover:bg-muted border-b border-border" : "folder-item parent-disabled cursor-not-allowed px-4 py-2 text-muted-fg";
                li.setAttribute("data-path", response.parent);
                li.textContent = ".. (parent)";
                folderList.appendChild(li);
            }
            (response.folders || []).forEach(function (item) {
                var li = document.createElement("li");
                li.className = item.type === "dir" ? "folder-item cursor-pointer px-4 py-2 hover:bg-muted border-b border-border" : "folder-item file-item cursor-pointer px-4 py-2 hover:bg-muted border-b border-border text-muted-fg";
                li.setAttribute("data-path", item.path);
                li.textContent = item.name;
                folderList.appendChild(li);
            });
            var titleEl = document.getElementById("folder-picker-modal-title");
            if (titleEl) titleEl.innerHTML = "Select Path: <code class=\"text-sm bg-muted px-1 rounded\">" + currentPath + "</code>";
        });
}

function browseFolderHandler(elementId) {
    activeInput = document.getElementById(elementId);
    if (currentPathType === "file") {
        currentPathType = "folder";
        currentPath += "/..";
    }
    loadFolder(currentPath);
    showFolderPickerModal();
}

let currentPath = "";
let currentPathType = "folder";
let browseWithFiles = false;
let activeInput = null;

document.addEventListener("DOMContentLoaded", function () {
    const folderList = document.getElementById("folder-list");
    if (folderList) {
        folderList.addEventListener("click", function (e) {
            const clicked = e.target.closest(".folder-item");
            if (!clicked) return;
            if (clicked.classList.contains("file-item")) {
                currentPath = clicked.getAttribute("data-path");
                const titleEl = document.getElementById("folder-picker-modal-title");
                if (titleEl) titleEl.innerHTML = "<b>Selected File:</b> <code class=\"text-sm bg-muted px-1 rounded\">" + currentPath + "</code>";
                currentPathType = "file";
            } else if (!clicked.classList.contains("parent-disabled")) {
                currentPath = clicked.getAttribute("data-path");
                if (currentPathType === "file") {
                    currentPathType = "folder";
                    currentPath += "/..";
                }
                loadFolder(currentPath);
            }
        });
    }

    const selectBtn = document.getElementById("select-folder-btn");
    if (selectBtn) {
        selectBtn.addEventListener("click", function () {
            if (activeInput) {
                activeInput.value = currentPath;
                activeInput.dispatchEvent(new Event("keyup", { bubbles: true }));
            }
            hideFolderPickerModal();
        });
    }

    document.querySelectorAll("[data-dismiss-modal='folder-picker-modal']").forEach(function (btn) {
        btn.addEventListener("click", hideFolderPickerModal);
    });
});
