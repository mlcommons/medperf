/*
 * Aggregator registration page.
 */

var REDIRECT_BASE = "/aggregators/ui/display/";

/** Enable the Register button only when the form is valid, and show the user what is missing (see form_validation.js). */
function checkAggregatorFormValidity() {
    var nameEl = document.getElementById("name");
    var addressEl = document.getElementById("address");
    var portEl = document.getElementById("port");
    var adminPortEl = document.getElementById("admin-port");
    var cubeEl = document.getElementById("aggregation-mlcube");
    var nameValue = nameEl ? nameEl.value.trim() : "";
    var addressValue = addressEl ? addressEl.value.trim() : "";
    var portValue = portEl && portEl.value ? parseInt(portEl.value, 10) : 0;
    var adminPortValue = adminPortEl && adminPortEl.value ? parseInt(adminPortEl.value, 10) : 0;
    var cubeValue = cubeEl && cubeEl.value ? parseInt(cubeEl.value, 10) : 0;
    var isValidPort = function (port) { return port > 0 && port <= 65535; };

    var problems = [];
    if (!nameValue) problems.push({ field: nameEl, message: "Enter the aggregator name" });
    if (!addressValue) problems.push({ field: addressEl, message: "Enter the aggregator address" });
    if (!isValidPort(portValue)) problems.push({ field: portEl, message: "Enter a port between 1 and 65535" });
    if (!isValidPort(adminPortValue)) problems.push({ field: adminPortEl, message: "Enter an admin port between 1 and 65535" });
    if (!(cubeValue > 0)) problems.push({ field: cubeEl, message: "Select the aggregation container" });

    var btn = document.getElementById("register-aggregator-btn");
    if (btn) btn.disabled = !showFormProblems(btn, problems);
}

/** Bind the registration form. */
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
