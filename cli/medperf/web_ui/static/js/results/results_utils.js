function showResult(element){
    const result = JSON.parse(element.getAttribute("data-result"));
    const resultPrettified = JSON.stringify(result, null, 2);

    const modalTitle = "Results";
    const modalBody = `<pre id="result-content" class="language-yaml">${resultPrettified}</pre>`
    const modalFooter = '<button type="button" class="btn btn-primary" data-bs-dismiss="modal" aria-label="Close">Close</button>';
    const extra_fn = () => { Prism.highlightElement($("#result-content")[0]); }

    showModal({
        title: modalTitle,
        body: modalBody,
        footer: modalFooter,
        modalClasses: "modal-lg",
        extra_func: extra_fn
    });
}