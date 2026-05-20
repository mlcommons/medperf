function showResult(element) {
    var resultStr = element.getAttribute("data-result");
    var result = {};
    try { result = JSON.parse(resultStr || "{}"); } catch (_) {}
    var resultPrettified = JSON.stringify(result, null, 2);
    var modalBody = "<pre id=\"result-content\" class=\"language-json overflow-x-auto p-4 rounded-lg bg-muted\">" + resultPrettified.replace(/</g, "&lt;") + "</pre>";
    var modalFooter = "<button type=\"button\" class=\"btn btn-sm btn-primary close-modal-btn\">Close</button>";
    var extra = function () {
        var el = document.getElementById("result-content");
        if (window.Prism && el) Prism.highlightElement(el);
    };
    showModal({
        title: "Results",
        body: modalBody,
        footer: modalFooter,
        modalClasses: "max-w-4xl w-full",
        extra_func: extra
    });
}
