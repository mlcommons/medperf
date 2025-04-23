
function showToast(message, bgClass) {
    const toastHTML = `
      <div class="toast align-items-center ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body fw-bold">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;

    const $toast = $(toastHTML);
    $("#toastContainer").append($toast);

    const bsToast = new bootstrap.Toast($toast[0], {
        animation: true,
        delay: 3000
    });

    bsToast.show();

    $toast.on("hidden.bs.toast", function () {
        $(this).remove();
    });
}

function changeNotificationCount(increment=true){
    const notification_count_element = $("#notifications-count");
    var notification_count = Number(notification_count_element.text());
    if (increment)
        notification_count += 1;
    else
        notification_count -= 1;
    notification_count_element.html(notification_count);
    if(notification_count > 0){
        if (notification_count_element.hasClass("d-none"))
            notification_count_element.removeClass("d-none");
    }
    else{
        if (!notification_count_element.hasClass("d-none"))
            notification_count_element.addClass("d-none");
    }
}

function addNotification(notification){
    const notifications_list = $("#notifications-list");
    let bgClass, borderClass
    if(!$(".notification-text").length){
        notifications_list.html("");
    }
    if (notification.type === "success"){
        bgClass = "bg-light text-success";
        borderClass = "border-success";
    }
    else if (notification.type === "info"){
        bgClass = "bg-light text-info";
        borderClass = "border-info";
    }
    else{
        bgClass = "bg-light text-danger";
        borderClass = "border-danger";
    }

    const fontWeight = !notification.read ? "fw-bold" : "";
    const mark_read_btn = $(`<button class="btn btn-sm btn-outline-secondary" data-id="${notification.id}" type="button">Mark as Read</button>`);
    const delete_btn = $(`<button class="btn btn-sm btn-outline-danger" data-id="${notification.id}" type="button">Delete</button>`);
    const new_notification = $(`
        <li class="dropdown-item" data-id=${notification.id} data-read=${notification.read}>
            <div class="d-flex flex-column mb-2 p-2 ${bgClass} border-2 border-bottom ${borderClass}">
                <div class="${fontWeight} notification-text" data-id=${notification.id}>${notification.message}</div>
                <div class="small text-muted">${timeAgo(notification.timestamp)}</div>
                <div class="mt-1 d-flex gap-2">
                </div>
            </div>
        </li>
    `);
    const buttonContainer = new_notification.find("div.mt-1.d-flex.gap-2");
    if (!notification.read) {
        buttonContainer.append(mark_read_btn);
    }
    buttonContainer.append(`<a href="${notification.url}" class="btn btn-sm btn-outline-primary">Open</a>`);
    buttonContainer.append(delete_btn);
    
    notifications_list.prepend(new_notification);
    if(!notification.read){
        changeNotificationCount();
        $(mark_read_btn).on("click", function(e) {
            const id = e.target.getAttribute("data-id");
            const current_button = e.target;
            $.ajax({
                url: "/notifications/mark_read",
                method: "post",
                data: { notification_id: id },
                async: true,
                success: function () {
                    const element = document.querySelector(`.notification-text[data-id="${id}"]`);
                    if(element)
                        element.classList.remove("fw-bold");
                    current_button.remove();
                    changeNotificationCount(false);
                },
                error: function (xhr, status, error) {
                    console.error("Failed to mark as read:", error);
                }
            });
        });
    }
    $(delete_btn).on("click", function(e) {
        const id = e.target.getAttribute("data-id");
        $.ajax({
            url: "/notifications/delete",
            method: "post",
            data: { notification_id: id },
            async: true,
            success: function () {
                deleteNotification(id);
            },
            error: function (xhr, status, error) {
                console.error("Failed to delete:", error);
            }
        });
    });
}

function getNotifications() {
    $.ajax({
        url: "/notifications",
        type: "GET",
        dataType: "json",
        async: true,
        success: function(response) {
            if (Array.isArray(response)) {
                response.forEach(function(notification) {
                    let bg = "text-bg-primary";
                    if (notification.type === "success")
                        bg = "text-bg-success";
                    else if (notification.type === "failed")
                        bg = "text-bg-danger";

                    showToast(notification.message, bg);
                    addNotification(notification);
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching notifications:', error);
        }
    });
}

function deleteNotification(notification_id){
    const element = document.querySelector(`.dropdown-item[data-id="${notification_id}"]`);
    if(element){
        element.remove();
        if(element.getAttribute("data-read") == "false")
            changeNotificationCount(false);
    }
    if(!$("#notifications-list > li").length){
        $("#notifications-list").append("<li class='dropdown-item'>No notifications yet</li>");
    }
}

function timeAgo(timestamp) {
    timestamp = timestamp * 1000;
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (seconds < 5)
        return "Just now";
    else if (seconds < 60)
        return `${seconds} seconds ago`
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60)
        return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24)
        return `${hours} hr${hours > 1 ? "s" : ""} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
}