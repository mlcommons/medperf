function checkAggregatorFormValidity() {
    var nameEl = document.getElementById("name");
    var addressEl = document.getElementById("address");
    var portEl = document.getElementById("port");
    var cubeEl = document.getElementById("aggregation-mlcube");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var addressValue = addressEl ? addressEl.value.trim() : "";
    var portValue = portEl && portEl.value ? parseInt(portEl.value, 10) : 0;
    var cubeValue = cubeEl && cubeEl.value ? parseInt(cubeEl.value, 10) : 0;
    var isValid = nameValue.length > 0 && addressValue.length > 0 && portValue > 0 && portValue <= 65535 && cubeValue > 0;
    var btn = document.getElementById("register-aggregator-btn");
    if (btn) btn.disabled = !isValid;
}

function init() {
    var form = document.getElementById("aggregator-register-form");
    if (form) {
        form.addEventListener("submit", submitActionForm);
        form.querySelectorAll("input, select").forEach(function (el) {
            el.addEventListener("keyup", checkAggregatorFormValidity);
            el.addEventListener("change", checkAggregatorFormValidity);
        });
    }
    checkAggregatorFormValidity();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
