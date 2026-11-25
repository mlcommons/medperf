/** Show the folder picker modal. */
function showFolderPickerModal() {
    const el = document.getElementById("folder-picker-modal");
    if (el) { el.classList.remove("hidden"); document.body.classList.add("overflow-hidden"); }
}
/** Hide the folder picker modal. */
function hideFolderPickerModal() {
    const el = document.getElementById("folder-picker-modal");
    if (el) { el.classList.add("hidden"); document.body.classList.remove("overflow-hidden"); }
}

/**
 * Show that a folder is loading: a spinner on the clicked item (or a loading
 * row if there is none), and the list, filter and Select button disabled.
 */
function setFolderLoading(loading, clickedItem) {
    folderLoading = loading;
    var folderList = document.getElementById("folder-list");
    var selectBtn = document.getElementById("select-folder-btn");
    var filterEl = document.getElementById("folder-filter");
    if (selectBtn) selectBtn.disabled = loading;
    // The filter is cleared when the new folder is listed: don't let the user type meanwhile
    if (filterEl) filterEl.disabled = loading;
    if (!folderList) return;
    folderList.setAttribute("aria-busy", loading ? "true" : "false");
    folderList.classList.toggle("cursor-wait", loading);
    folderList.querySelectorAll(".folder-item").forEach(function (item) {
        item.classList.toggle("opacity-50", loading && item !== clickedItem);
    });
    if (!loading) return;
    var errorItem = folderList.querySelector(".folder-error");
    if (errorItem) errorItem.remove();
    if (clickedItem) {
        clickedItem.classList.add("flex", "items-center", "justify-between");
        addSpinner(clickedItem);
    } else {
        folderList.innerHTML = "<li class=\"folder-loading flex items-center gap-2 px-4 py-2 text-muted-fg\"><span class=\"" + STAGE_SPINNER_CLASS + "\" aria-hidden=\"true\"></span>Loading...</li>";
    }
}

/** Show why a folder could not be listed, keeping the current list usable. */
function showFolderError(path, message) {
    var folderList = document.getElementById("folder-list");
    if (!folderList) return;
    var loadingItem = folderList.querySelector(".folder-loading");
    if (loadingItem) loadingItem.remove();
    folderList.querySelectorAll(".folder-item").forEach(function (item) {
        var spinner = item.querySelector(".animate-spin");
        if (spinner) spinner.remove();
    });
    var li = document.createElement("li");
    li.className = "folder-error px-4 py-2 text-danger-fg bg-danger-muted";
    var name = path.replace(/\/+$/, "").split("/").pop() || path;
    li.textContent = "Cannot open \"" + name + "\": " + message;
    folderList.insertBefore(li, folderList.firstChild);
}

/** Show only the items of the listed folder whose name contains the filter text. */
function filterFolderList() {
    var filterEl = document.getElementById("folder-filter");
    var folderList = document.getElementById("folder-list");
    if (!filterEl || !folderList) return;
    var query = filterEl.value.trim().toLowerCase();
    var matches = 0;
    folderList.querySelectorAll(".folder-item:not(.parent-item)").forEach(function (item) {
        item.hidden = item.textContent.toLowerCase().indexOf(query) === -1;
        if (!item.hidden) matches++;
    });
    var noMatchItem = folderList.querySelector(".folder-no-match");
    if (noMatchItem) noMatchItem.remove();
    if (query && !matches) {
        var li = document.createElement("li");
        li.className = "folder-no-match px-4 py-2 text-muted-fg";
        li.textContent = "No items match \"" + filterEl.value.trim() + "\"";
        folderList.appendChild(li);
    }
}

/** List the content of a folder in the picker (files only if browseWithFiles). */
function loadFolder(path, clickedItem) {
    var requestId = ++folderRequestId;
    setFolderLoading(true, clickedItem);
    var formData = new FormData();
    formData.append("path", path);
    formData.append("with_files", browseWithFiles);
    fetch("/api/browse", { method: "POST", body: formData })
        .then(function (r) {
            return r.json().catch(function () { return { error: "unexpected server error (" + r.status + ")" }; })
                .then(function (body) {
                    if (!r.ok) throw new Error(body.error || r.statusText);
                    return body;
                });
        })
        .then(function (response) {
            if (requestId !== folderRequestId) return;
            setFolderLoading(false);
            currentPath = response.current_folder || "";
            currentPathType = "folder";
            var folderList = document.getElementById("folder-list");
            if (!folderList) return;
            folderList.innerHTML = "";
            if (response.parent) {
                var li = document.createElement("li");
                li.className = response.have_parent ? "folder-item parent-item cursor-pointer px-4 py-2 hover:bg-muted border-b border-border" : "folder-item parent-item parent-disabled cursor-not-allowed px-4 py-2 text-muted-fg";
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
            if (titleEl) titleEl.innerHTML = "Select Path: <code class=\"text-sm bg-muted px-1 rounded\">" + escapeHtml(currentPath) + "</code>";
            var filterEl = document.getElementById("folder-filter");
            if (filterEl) {
                filterEl.value = "";
                filterEl.focus({ preventScroll: true });
            }
        })
        .catch(function (error) {
            if (requestId !== folderRequestId) return;
            setFolderLoading(false);
            showFolderError(path, error.message);
        });
}

/** Open the picker to fill the input with the given ID. */
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
let folderLoading = false;
let folderRequestId = 0;

document.addEventListener("DOMContentLoaded", function () {
    const folderList = document.getElementById("folder-list");
    if (folderList) {
        folderList.addEventListener("click", function (e) {
            const clicked = e.target.closest(".folder-item");
            if (!clicked || folderLoading) return;
            if (clicked.classList.contains("file-item")) {
                currentPath = clicked.getAttribute("data-path");
                const titleEl = document.getElementById("folder-picker-modal-title");
                if (titleEl) titleEl.innerHTML = "<b>Selected File:</b> <code class=\"text-sm bg-muted px-1 rounded\">" + escapeHtml(currentPath) + "</code>";
                currentPathType = "file";
            } else if (!clicked.classList.contains("parent-disabled")) {
                loadFolder(clicked.getAttribute("data-path"), clicked);
            }
        });
    }

    const filterEl = document.getElementById("folder-filter");
    if (filterEl) filterEl.addEventListener("input", filterFolderList);

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
