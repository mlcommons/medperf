/*
 * The page modal (#page-modal in base.html), shared by all dialogs.
 *
 * Only one dialog is shown at a time: requesting a modal while another one is
 * open queues it until the current one is closed. Exposes showModal,
 * requestModal, hidePageModal, onModalHidden and resetModal on `window`.
 */

(function () {
    "use strict";

    const modalId = "page-modal";
    const dialogId = "page-modal-dialog";
    const titleId = "page-modal-title";
    const bodyId = "page-modal-body";
    const footerId = "page-modal-footer";

    window.modalQueue = window.modalQueue || [];
    window.modalOpen = window.modalOpen || false;

    /** Shortcut for document.getElementById. */
    function getEl(id) {
        return document.getElementById(id);
    }

    const dialogBaseClass = "rounded-2xl shadow-xl w-full mx-auto relative bg-card dark:bg-card border-2 border-border-brand dark:border-border max-h-[90vh] flex flex-col scale-95 transition-transform duration-300 ease-out";

    /** Reset the modal to its default size and empty content. */
    function resetModal() {
        const dialog = getEl(dialogId);
        const title = getEl(titleId);
        if (dialog) dialog.setAttribute("class", dialogBaseClass + " max-w-md");
        if (title) title.setAttribute("class", "text-xl font-bold text-brand-accent");
        if (getEl(bodyId)) getEl(bodyId).innerHTML = "";
        if (getEl(footerId)) getEl(footerId).innerHTML = "";
    }

    /**
     * Fill the modal with the given options and show it.
     *
     * @param {Object} options - title, body and footer (HTML), titleClasses,
     *     modalClasses (dialog size), extra_func (called once the content is set).
     */
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
        titleEl.setAttribute("class", "text-xl font-bold text-brand-accent " + (titleClasses || ""));
        titleEl.innerHTML = title;
        bodyEl.innerHTML = body;
        bodyEl.classList.add("text-ink");
        footerEl.innerHTML = footer;

        if (typeof extra_func === "function") extra_func();

        modalEl.classList.add("modal-visible");
        if (dialog) dialog.classList.add("scale-100");
        modalEl.setAttribute("aria-hidden", "false");
        document.body.classList.add("overflow-hidden");
    }

    /** Hide the modal (the next queued one, if any, is shown by onModalHidden). */
    function hideModal() {
        const modalEl = getEl(modalId);
        const dialog = getEl(dialogId);
        if (!modalEl) return;
        modalEl.classList.remove("modal-visible");
        if (dialog) dialog.classList.remove("scale-100");
        modalEl.setAttribute("aria-hidden", "true");
        document.body.classList.remove("overflow-hidden");
    }

    /** Show the next queued modal, if any. Must be called after hiding the modal. */
    function onModalHidden() {
        window.modalOpen = false;
        if (window.modalQueue.length > 0) {
            const next = window.modalQueue.shift();
            window.modalOpen = true;
            next();
        }
    }

    /** Run `showFn` now if no modal is open, or once the open ones are closed. */
    function requestModal(showFn) {
        if (!window.modalOpen) {
            window.modalOpen = true;
            showFn();
        } else {
            window.modalQueue.push(showFn);
        }
    }

    /** Show a modal (queued if another one is open). See showModalImpl for the options. */
    function showModal(options) {
        requestModal(function () {
            showModalImpl(options);
        });
    }

    /** Close the modal when clicking its backdrop or close button. */
    function bindPageModal() {
        const modalEl = getEl(modalId);
        if (!modalEl) return;

        const backdrop = document.getElementById("page-modal-backdrop");
        const closeBtn = document.getElementById("page-modal-close-btn");

        /** Hide the modal and show the next queued one. */
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
