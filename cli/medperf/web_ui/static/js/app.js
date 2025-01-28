let currentStageElement, datasetId, logPanel, stagesList;
    
document.addEventListener('DOMContentLoaded', function() {
    currentStageElement = null;
    logPanel = document.getElementById('log-panel');
    stagesList = document.getElementById('stages-list');
});

function showReloadModal(title){
    $("#promptTitle").html(title);
    const promptModal = new bootstrap.Modal('#promptModal', {
        keyboard: false,
        backdrop: "static"
    })
    promptModal.show();
}

function timer(seconds, url=null){
    $("#promptText").html(`The window will reload in <span id='timer'>${seconds}</span> ...`);
    const timerInterval = setInterval(function() {
        seconds--;
        $("#timer").text(seconds);

        if (seconds === 0) {
            clearInterval(timerInterval);
            if(!url)
                window.location.reload(true);
            else
                window.location.href = url;
        }
    }, 1000);
}

function markAllStagesAsComplete(){
    // Mark all stages as completed
    document.querySelectorAll("#stages-list > li").forEach(el => {
        markStageAsComplete(el);
    });
}

function showResult(element){
    const result = JSON.parse(element.getAttribute("data-result"));
    const dataset_name = element.getAttribute("data-dataset-name");
    const benchmark_name = element.getAttribute("data-benchmark-name");
    const model_name = element.getAttribute("data-model-name");
    $("#result-content").html(JSON.stringify(result, null, 2));
    $("#resultModalLabel").html(`Result for Benchmark '${benchmark_name}' - Dataset '${dataset_name}' - Model '${model_name}'`);
    const resultModal = new bootstrap.Modal('#resultModal', {
        keyboard: false,
        backdrop: "static"
    })
    resultModal.show();
    Prism.highlightElement(document.getElementById("result-content"));
}

function submitResult(element){
    const result_name = element.getAttribute("data-result-name");
    $.ajax({
        url: "/datasets/result_submit",
        type: "POST",
        data: { result_id: result_name },
        dataType: "json",
        async: true,
        success: function(response) {
            let title;
            if(response){
                title = "Successfully Submitted Results";
            }
            else{
                title = "Failed to Submit Results";
            }
            showReloadModal(title);
            timer(3);
        },
        error: function(xhr, status, error) {
            console.error('Error preparing:', error); // TODO
        }
    });
    getEvents(logPanel, stagesList, currentStageElement);
}

function showPanel(title){
    $("#panel-title").text(title);
    $("#panel").show();
    scroll("log-panel");
}

function scroll(element_id){
    $("html, body").animate({
        scrollTop: $(`#${element_id}`).offset().top
    }, 1000);
}

function runBenchmark(element, benchmark_id=null, dataset_id=null, model_ids=null, dataset_name=null){
    let text;
    var formData = new FormData();
    if(benchmark_id){
        model_names = [];
        model_ids.forEach(model => {
            formData.append("model_ids", model.id);
            model_names.push(model.name);
        });
        model_names = model_names.join(" - ")
        text = `Evaluating Models '${model_names}' on Dataset '${dataset_name}'...`;
    }
    else{
        model_ids = element.getAttribute("data-model-id");
        benchmark_id = element.getAttribute("data-benchmark-id");
        dataset_id = element.getAttribute("data-dataset-id");
        model_name = element.getAttribute("data-model-name");
        dataset_name = element.getAttribute("data-dataset-name");
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Running
        `; 
        element.setAttribute("disabled", true);
        text = `Evaluating Model '${model_name}' on Dataset '${dataset_name}'...`;
        formData.append("model_ids", model_ids);
        
    }
    formData.append("dataset_id", dataset_id);
    formData.append("benchmark_id", benchmark_id);
    
    // Append each model_id individually to the FormData object
    //model_ids.forEach((model_id) => {
    //    formData.append("model_ids", model_id);
    //});
    $.ajax({
        url: "/datasets/run",
        type: "POST",
        data: formData,
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            let title;
            if(response){
                title = "Successfully Ran Execution.";
            }
            else{
                title = "Failed to Run Execution.";
            }
            showReloadModal(title);
            timer(3);
        },
        error: function(xhr, status, error) {
            console.error('Error preparing:', error); // TODO
        }
    });
    
    showPanel(text);
    getEvents(logPanel, stagesList, currentStageElement);
}

function associate(dataset_id, benchmark_id, dataset_name){
    document.getElementById("dropdown-div").classList.remove("show");
    const associate_btn = document.getElementById("associate-dropdown");
    associate_btn.setAttribute("disabled", true);
    associate_btn.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Associating
    `;
    $.ajax({
        url: "/datasets/associate",
        type: "POST",
        data: { dataset_id: dataset_id, benchmark_id: benchmark_id },
        dataType: "json",
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            let title;
            if(response){
                title = "Successfully Associated Dataset.";
            }
            else{
                title = "Failed to Associate Dataset.";
            }
            showReloadModal(title);
            timer(3);
        },
        error: function(xhr, status, error) {
            console.error('Error Associating:', error); // TODO
        }
    });
    showPanel(`Associating dataset '${dataset_name}'...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function setOperation(element){
    const dataset_id = element.getAttribute("data-dataset-id");
    element.setAttribute("disabled", true);
    element.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Setting Operational
    `;
    $.ajax({
        url: "/datasets/set_operational",
        type: "POST",
        data: { dataset_id: dataset_id },
        dataType: "json",
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            let title;
            if(response.dataset_id){
                title = "Successfully Set Dataset Into Operation";
            }
            else{
                title = "Failed Set Dataset Into Operation";
            }
            showReloadModal(title);
            timer(3);
        },
        error: function(xhr, status, error) {
            console.error('Error setting operational:', error); // TODO
        }
    });
    getEvents(logPanel, stagesList, currentStageElement);
}

function prepare(element) {
    const dataset_id = element.getAttribute("data-dataset-id");
    const dataset_name = element.getAttribute("data-dataset-name");
    element.setAttribute("disabled", true);
    element.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Preparing
    `;
    $.ajax({
        url: "/datasets/prepare",
        type: "POST",
        data: { dataset_id: dataset_id },
        dataType: "json",
        async: true,
        success: function(response) {
            let title;
            markAllStagesAsComplete();
            if(response.dataset_id!==null){
                title = "Successfully Prepared Dataset.";
            }
            else{
                title = "Failed to Prepare Dataset.";
            }
            showReloadModal(title);
            timer(3);

        },
        error: function(xhr, status, error) {
            console.error('Error preparing:', error); // TODO
        }
    });
    showPanel(`Preparing dataset '${dataset_name}'...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function submitDataset(){
    const formData = new FormData($("#dataset-form")[0]);
    $.ajax({
        url: "/datasets/submit",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response.dataset_id!==null){
                showReloadModal("Dataset Successfully Submitted.");
                timer(3, url="/datasets/ui/display/"+response.dataset_id);
            }
            else{
                showReloadModal("Dataset Submission Cancelled.");
                timer(3);
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    $("#step-3").hide();
    getEvents(logPanel, stagesList, currentStageElement);
}

function testMLCube(){
    const runBtn = $("#run-test");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Running
    `);
    const formData = new FormData($("#mlcube-form")[0]);
    $.ajax({
        url: "/mlcubes/test",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response){
                const nextModal = new bootstrap.Modal('#nextModal', {
                    keyboard: false,
                    backdrop: "static"
                })
                nextModal.show();
            }
            else{
                showReloadModal("Model Compatibility Test Failed.");
                timer(3);
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    showPanel(`Running Compatibility Test...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkInput() {
    // Get elements
    const benchmark = document.getElementById("benchmark");
    const formFilePath = document.getElementById("model_path");
    const runTestButton = document.getElementById("run-test");
  
    // Ensure values are being retrieved
    const benchmarkValue = benchmark ? benchmark.value : "";
    const filePathValue = formFilePath ? formFilePath.value.trim() : "";
  
    // Validate inputs
    const isBenchmarkSelected = benchmarkValue !== "";
    const isFilePathValid = filePathValue.length > 0 && filePathValue.endsWith(".yaml");
  
    // Enable/disable button
    runTestButton.disabled = !(isBenchmarkSelected && isFilePathValid);
}

function submitMLCube(){
    const runBtn = $("#submit-btn");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Submitting
    `);
    const formData = new FormData($("#submit-form")[0]);
    $.ajax({
        url: "/mlcubes/submit",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response){
                showReloadModal("Successfully submitted MLCube");
                timer(3, url="/mlcubes/ui/display/"+1); // TODO
            }
            else{
                showReloadModal("Failed to submit MLCube.");
                timer(3);
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    showPanel(`Submitting MLCube...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkSubmit(){
    // Get elements
    const mlcube = document.getElementById("mlcube_file");
    const parameters = document.getElementById("parameters_file");
    const additional = document.getElementById("additional_file");
    const submitBtn = document.getElementById("submit-btn");
    
    // Ensure values are being retrieved
    const mlcubeValue = mlcube ? mlcube.value.trim() : "";
    const parametersValue = parameters ? parameters.value.trim() : "";
    const additionalValue = additional ? additional.value.trim() : "";
  
    // Validate inputs
    const isMLCubeValid = mlcubeValue.length > 0 && mlcubeValue.endsWith(".yaml");
    const isParametersValid = parametersValue.length > 0 && parametersValue.endsWith(".yaml");
    const isadditionalValid = additionalValue.length > 0 && additionalValue.endsWith(".tar.gz");
  
    // Enable/disable button
    submitBtn.disabled = !(isMLCubeValid && isParametersValid && isadditionalValid);
}

function cancelSubmit(){
    window.location.reload(true);
}

function showSubmit(){
    window.location.href = "/mlcubes/submit/ui";
}

function associateMLCube(mlcube_id, benchmark_id, mlcube_name){
    document.getElementById("dropdown-div").classList.remove("show");
    const associate_btn = document.getElementById("associate-dropdown");
    associate_btn.setAttribute("disabled", true);
    associate_btn.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Associating
    `;
    $.ajax({
        url: "/mlcubes/associate",
        type: "POST",
        data: { mlcube_id: mlcube_id, benchmark_id: benchmark_id },
        dataType: "json",
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            let title;
            if(response){
                title = "Successfully Associated MLCube.";
            }
            else{
                title = "Failed to Associate MLCube.";
            }
            showReloadModal(title);
            timer(3);
        },
        error: function(xhr, status, error) {
            console.error('Error Associating:', error); // TODO
        }
    });
    showPanel(`Associating MLCube '${mlcube_name}'...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function cleanPanel(){
    $("#panel").hide();
    $("#panel-title").html("");
    $("#stages-list").html("");
    $("#log-panel").html("");
}

function getMLCubes(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/mlcubes/ui?mine_only="+mine_only;
}

function getDatasets(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/datasets/ui?mine_only="+mine_only;
}

function respond_yes(){
    $.ajax({
        url: "/datasets/events",
        type: "POST",
        data: { is_approved: true },
    });
}
function respond_no(){
    $.ajax({
        url: "/datasets/events",
        type: "POST",
        data: { is_approved: false },
    });
}
function showLoading(){
    $("#loading-overlay").css("display", "flex");
    $("html").css("cursor", "not-allowed");
}
function hideLoading(){
    $("#loading-overlay").hide();
    $("html").css("cursor", "unset");
}