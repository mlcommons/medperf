function showToast(title, message, bgClass) {
    const toastStyles = {
        "text-bg-primary": { bg: "bg-info", fg: "text-white" },
        "text-bg-success": { bg: "bg-brand", fg: "text-ink" },
        "text-bg-danger": { bg: "bg-danger", fg: "text-white" },
        "text-bg-info": { bg: "bg-info", fg: "text-white" },
    };
    const style = toastStyles[bgClass] || { bg: "bg-muted-strong", fg: "text-ink" };
    const toastHTML = `
      <div class="toast-item flex items-center gap-3 ${style.bg} ${style.fg} rounded-xl shadow-lg px-4 py-3 border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="flex-1 min-w-0">
          <strong class="block">${title}</strong>
          <span class="text-sm opacity-90">${message}</span>
        </div>
        <button type="button" class="toast-close flex-shrink-0 w-8 h-8 rounded-lg hover:bg-white/20 flex items-center justify-center text-lg leading-none cursor-pointer" aria-label="Close">&times;</button>
      </div>
    `;
    const el = document.createElement("div");
    el.innerHTML = toastHTML.trim();
    const toastEl = el.firstChild;
    toastEl.classList.add("pointer-events-auto");
    const container = document.getElementById("toast-container");
    if (container) container.appendChild(toastEl);

    toastEl.querySelector(".toast-close").addEventListener("click", () => {
        toastEl.remove();
    });
    setTimeout(() => toastEl.remove(), 5000);
}

function changeNotificationCount(increment) {
    const el = document.getElementById("notifications-count");
    if (!el) return;
    let n = parseInt(el.textContent, 10) || 0;
    n = increment ? n + 1 : Math.max(0, n - 1);
    el.textContent = n;
    if (n > 0) el.classList.remove("hidden");
    else el.classList.add("hidden");
}

function addNotification(notification) {
    const list = document.getElementById("notifications-list");
    if (!list) return;
    if (!list.querySelector(".notification-text")) list.innerHTML = "";

    let bgClass = "bg-muted text-ink border-border";
    if (notification.type === "success") {
        bgClass = "bg-success-muted text-success border-success";
    } else if (notification.type === "info") {
        bgClass = "bg-info-muted text-info-fg border-info";
    } else {
        bgClass = "bg-danger-muted text-danger-fg border-danger";
    }

    const fontWeight = !notification.read ? "font-bold" : "";
    const markReadBtn = `<button class="mark-read-btn btn btn-xs btn-secondary" data-id="${notification.id}" type="button">Mark as Read</button>`;
    const deleteBtn = `<button class="delete-notif-btn btn btn-xs btn-danger hover:bg-danger-muted cursor-pointer" data-id="${notification.id}" type="button">Delete</button>`;
    let buttons = "";
    if (!notification.read) buttons += markReadBtn;
    if (notification.url) {
        buttons += `<a href="${notification.url}" class="btn btn-xs btn-secondary">Open</a>`;
    }
    buttons += deleteBtn;

    const li = document.createElement("li");
    li.className = "px-4 py-3 border-b border-border";
    li.setAttribute("data-id", notification.id);
    li.setAttribute("data-read", notification.read);
    li.innerHTML = `
      <div class="flex flex-col p-2 rounded-lg border-2 ${bgClass}">
        <div class="${fontWeight} notification-text" data-id="${notification.id}">${notification.message}</div>
        <div class="text-xs text-muted-fg mt-1">${timeAgo(notification.timestamp)}</div>
        <div class="mt-2 flex flex-wrap gap-2">${buttons}</div>
      </div>
    `;

    list.insertBefore(li, list.firstChild);

    if (!notification.read) changeNotificationCount(true);

    var markReadBtnEl = li.querySelector(".mark-read-btn");
    if (markReadBtnEl) markReadBtnEl.addEventListener("click", function () {
        var id = this.getAttribute("data-id");
        var fd = new FormData();
        fd.append("notification_id", id);
        fetch("/notifications/mark_read", { method: "POST", body: fd }).then(function () {
            var textEl = document.querySelector(".notification-text[data-id=\"" + id + "\"]");
            if (textEl) textEl.classList.remove("font-bold");
            var btn = li.querySelector(".mark-read-btn");
            if (btn) btn.remove();
            changeNotificationCount(false);
        });
    });
    var deleteBtnEl = li.querySelector(".delete-notif-btn");
    if (deleteBtnEl) deleteBtnEl.addEventListener("click", function () {
        var id = this.getAttribute("data-id");
        var fd = new FormData();
        fd.append("notification_id", id);
        fetch("/notifications/delete", { method: "POST", body: fd }).then(function () { deleteNotification(id); });
    });
}

function processNotification(notification) {
    let bg = "text-bg-primary";
    if (notification.type === "success") bg = "text-bg-success";
    else if (notification.type === "failed") bg = "text-bg-danger";
    showToast("New Notification", notification.message, bg);
    addNotification(notification);
}

function deleteNotification(notification_id) {
    const el = document.querySelector(`#notifications-list [data-id="${notification_id}"]`);
    if (el) {
        if (el.getAttribute("data-read") === "false") changeNotificationCount(false);
        el.remove();
    }
    const list = document.getElementById("notifications-list");
    if (list && !list.querySelector("li[data-id]")) {
        const empty = document.createElement("li");
        empty.className = "px-4 py-3 text-muted-fg text-sm";
        empty.textContent = "No notifications yet";
        list.appendChild(empty);
    }
}

function timeAgo(timestamp) {
    timestamp = timestamp * 1000;
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (seconds < 5) return "Just now";
    if (seconds < 60) return `${seconds} seconds ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr${hours > 1 ? "s" : ""} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
}
