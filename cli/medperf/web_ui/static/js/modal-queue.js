(function () {
    "use strict";

    const modalId = "page-modal";
    const dialogId = "page-modal-dialog";
    const titleId = "page-modal-title";
    const bodyId = "page-modal-body";
    const footerId = "page-modal-footer";

    window.modalQueue = window.modalQueue || [];
    window.modalOpen = window.modalOpen || false;

    function getEl(id) {
        return document.getElementById(id);
    }

    const dialogBaseClass = "rounded-2xl shadow-xl w-full mx-auto relative bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-gray-700 max-h-[90vh] flex flex-col scale-95 transition-transform duration-300 ease-out";

    function resetModal() {
        const dialog = getEl(dialogId);
        const title = getEl(titleId);
        if (dialog) dialog.setAttribute("class", dialogBaseClass + " max-w-md");
        if (title) title.setAttribute("class", "text-xl font-bold medperf-accent dark:text-green-400");
        if (getEl(bodyId)) getEl(bodyId).innerHTML = "";
        if (getEl(footerId)) getEl(footerId).innerHTML = "";
    }

    function showModalImpl(options) {
        const {
            title = "",
            body = "",
            footer = "",
            titleClasses = "",
            modalClasses = "",
            extra_func = null,
        } = options;

        resetModal();

        const dialog = getEl(dialogId);
        const titleEl = getEl(titleId);
        const bodyEl = getEl(bodyId);
        const footerEl = getEl(footerId);
        const modalEl = getEl(modalId);

        if (!modalEl || !titleEl || !bodyEl || !footerEl) return;

        if (dialog) {
            const sizeClass = (modalClasses || "").trim();
            dialog.setAttribute("class", (sizeClass ? sizeClass + " " : "max-w-md ") + dialogBaseClass);
        }
        titleEl.setAttribute("class", "text-xl font-bold medperf-accent dark:text-green-400 " + (titleClasses || ""));
        titleEl.innerHTML = title;
        bodyEl.innerHTML = body;
        bodyEl.classList.add("text-gray-900", "dark:text-white");
        footerEl.innerHTML = footer;

        if (typeof extra_func === "function") extra_func();

        modalEl.classList.add("modal-visible");
        if (dialog) dialog.classList.add("scale-100");
        modalEl.setAttribute("aria-hidden", "false");
        document.body.classList.add("overflow-hidden");
    }

    function hideModal() {
        const modalEl = getEl(modalId);
        const dialog = getEl(dialogId);
        if (!modalEl) return;
        modalEl.classList.remove("modal-visible");
        if (dialog) dialog.classList.remove("scale-100");
        modalEl.setAttribute("aria-hidden", "true");
        document.body.classList.remove("overflow-hidden");
    }

    function onModalHidden() {
        window.modalOpen = false;
        if (window.modalQueue.length > 0) {
            const next = window.modalQueue.shift();
            window.modalOpen = true;
            next();
        }
    }

    function requestModal(showFn) {
        if (!window.modalOpen) {
            window.modalOpen = true;
            showFn();
        } else {
            window.modalQueue.push(showFn);
        }
    }

    function showModal(options) {
        requestModal(function () {
            showModalImpl(options);
        });
    }

    function bindPageModal() {
        const modalEl = getEl(modalId);
        if (!modalEl) return;

        const backdrop = document.getElementById("page-modal-backdrop");
        const closeBtn = document.getElementById("page-modal-close-btn");

        function close() {
            hideModal();
            onModalHidden();
        }

        if (backdrop) backdrop.addEventListener("click", close);
        if (closeBtn) closeBtn.addEventListener("click", close);

        modalEl.addEventListener("click", function (e) {
            if (e.target === modalEl) close();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindPageModal);
    } else {
        bindPageModal();
    }

    window.showModal = showModal;
    window.requestModal = requestModal;
    window.hidePageModal = hideModal;
    window.onModalHidden = onModalHidden;
    window.resetModal = resetModal;
})();
