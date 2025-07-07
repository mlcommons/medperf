function showResult(element){
    const result = JSON.parse(element.getAttribute("data-result"));

    $("#result-content").html(JSON.stringify(result, null, 2));
    $("#result-modal-title").html(`Results`);
    const resultModal = new bootstrap.Modal('#result-modal', {
        keyboard: false,
        backdrop: "static"
    })
    resultModal.show();
    Prism.highlightElement($("#result-content")[0]);
}