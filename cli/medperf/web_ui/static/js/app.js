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
    $("#resultModalLabel").html(`Benchmark Results`);
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
            if(response.status === "success"){
                title = "Results Successfully Submitted";
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Results Submission Failed";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
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
    
    $.ajax({
        url: "/datasets/run",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            let title;
            if(response.status === "success"){
                title = "Execution Ran Successfully";
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Execution Failed";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
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
    Requesting Association
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
                title = "Association Requested Successfully";
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Association Request Failed";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error Associating:', error); // TODO
        }
    });
    showPanel(`Requesting Association...`);
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
            console.log(response.error);
            markAllStagesAsComplete();
            let title;
            if(response.status === "success"){
                title = "Dataset Set to Operation Successfully"
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Failed to Set Dataset to Operation"
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
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
            if(response.status === "success"){
                title = "Dataset Prepared Successfully";
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Failed to Prepare Dataset";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
            showReloadModal(title);
            timer(3);

        },
        error: function(xhr, status, error) {
            console.error('Error preparing:', error); // TODO
        }
    });
    showPanel(`Preparing Dataset...`);
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
            let title;
            markAllStagesAsComplete();
            if(response.status === "success"){
                title = "Dataset Registered Successfully";
                showReloadModal(title);
                timer(3, url="/datasets/ui/display/"+response.dataset_id);
            }
            else{
                title = "Dataset Registration Canceled";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
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
    const input_elements = document.querySelectorAll("input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const select_elements = document.querySelectorAll("select");
    select_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/mlcubes/test",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response.status === "success"){
                const nextModal = new bootstrap.Modal('#nextModal', {
                    keyboard: false,
                    backdrop: "static"
                })
                $("#yaml-content").html(JSON.stringify(response.results, null, 2));
                Prism.highlightElement(document.getElementById("yaml-content"));
                nextModal.show();
            }
            else{
                $("#errorModalLabel").html("Model Compatibility Test Failed");
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
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

function checkInputBenchmark() {
    // Get elements
    const data_preparation = document.getElementById("data_preparation");
    const model_path = document.getElementById("model_path");
    const evaluator_path = document.getElementById("evaluator_path");
    const data_path = document.getElementById("data_path");
    const labels_path = document.getElementById("labels_path");
    const runTestButton = document.getElementById("run-test");
  
    // Ensure values are being retrieved
    const dataPreparationValue = data_preparation ? data_preparation.value : "";
    const modelPathValue = model_path ? model_path.value.trim() : "";
    const evaluatorPathValue = evaluator_path ? evaluator_path.value : "";
    const dataPathValue = data_path ? data_path.value.trim() : "";
    const labelsPathValue = labels_path ? labels_path.value : "";
  
    // Validate inputs
    const dataPreparationValid = dataPreparationValue.length > 0 && dataPreparationValue.endsWith(".yaml");
    const modelPathValid = modelPathValue.length > 0 && modelPathValue.endsWith(".yaml");
    const evaluatorPathValid = evaluatorPathValue.length > 0 && evaluatorPathValue.endsWith(".yaml");
    const dataPathValid = dataPathValue.length > 0;
    const labelsPathValid = labelsPathValue.length > 0;

  
    // Enable/disable button
    runTestButton.disabled = !(
        dataPreparationValid && modelPathValid && evaluatorPathValid && dataPathValid && labelsPathValid
    );
}

function submitMLCube(){
    const runBtn = $("#submit-btn");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Registering
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
            if(response.status === "success"){
                showReloadModal("Model Registered Successfully");
                timer(3, url="/mlcubes/ui/display/"+response.mlcube_id);
            }
            else{
                $("#errorModalLabel").html("Failed to Register Model");
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    showPanel(`Registering Model...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function checkSubmit(){
    // Get elements
    const name = document.getElementById("name");
    const mlcube = document.getElementById("mlcube_file");
    const submitBtn = document.getElementById("submit-btn");
    
    // Ensure values are being retrieved
    const mlcubeValue = mlcube ? mlcube.value.trim() : "";
    const nameValue = name ? name.value.trim() : "";
  
    // Validate inputs
    const isMLCubeValid = mlcubeValue.length > 0 && mlcubeValue.endsWith(".yaml");
    const isNameValid = nameValue.length > 0;

    // Enable/disable button
    submitBtn.disabled = !(isMLCubeValid && isNameValid);
}

function checkSubmitBenchmark(){
    // Get elements
    const name = document.getElementById("name");
    const description = document.getElementById("description");
    const demo_url = document.getElementById("demo_url");
    const data_preparation_mlcube = document.getElementById("data_preparation_mlcube");
    const reference_model_mlcube = document.getElementById("reference_model_mlcube");
    const evaluator_mlcube = document.getElementById("evaluator_mlcube");
    const submitBtn = document.getElementById("submit-btn");
    
    // Ensure values are being retrieved
    const nameValue = name ? name.value.trim() : "";
    const descriptionValue = description ? description.value.trim() : "";
    const demoUrlValue = demo_url ? demo_url.value.trim() : "";
    const dataPreparationMLCubeValue = data_preparation_mlcube ? Number(data_preparation_mlcube.value.trim()) : 0;
    const referenceModelMLCubeValue = reference_model_mlcube ? Number(reference_model_mlcube.value.trim()) : 0;
    const evaluatorMLCubeValue = evaluator_mlcube ? Number(evaluator_mlcube.value.trim()) : 0;
  
    // Validate inputs
    const isNameValid = nameValue.length > 0;
    const isDescriptionValid = descriptionValue.length > 0;
    const isDemoUrlValid = demoUrlValue.length > 0 && demoUrlValue.endsWith(".tar.gz");
    const isDataPreparationMLCubeValid = dataPreparationMLCubeValue > 0;
    const isReferenceModelMLCubeValid = referenceModelMLCubeValue > 0;
    const isEvaluatorMLCubeValid = evaluatorMLCubeValue > 0;
  
    // Enable/disable button
    submitBtn.disabled = !(
        isNameValid && isDescriptionValid && isDemoUrlValid && isDataPreparationMLCubeValid && isReferenceModelMLCubeValid && isEvaluatorMLCubeValid
    );
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
    Requesting Association
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
            if(response.status === "success"){
                title = "Association Requested Successfully";
                showReloadModal(title);
                timer(3);
            }
            else{
                title = "Association Request Failed";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error Associating:', error); // TODO
        }
    });
    showPanel(`Requesting Model Association...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function testBenchmark(){
    const runBtn = $("#run-test");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Running
    `);
    const formData = new FormData($("#test-form")[0]);
    const input_elements = document.querySelectorAll("input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const select_elements = document.querySelectorAll("select");
    select_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/benchmarks/test",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response.status === "success"){
                const nextModal = new bootstrap.Modal('#nextModal', {
                    keyboard: false,
                    backdrop: "static"
                })
                $("#yaml-content").html(JSON.stringify(response.results, null, 2));
                Prism.highlightElement(document.getElementById("yaml-content"));
                nextModal.show();
            }
            else{
                $("#errorModalLabel").html("Benchmark Workflow Test Failed");
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    showPanel(`Running Workflow Test...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function submitBenchmark(){
    const runBtn = $("#submit-btn");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Registering
    `);
    const formData = new FormData($("#submit-form")[0]);
    $.ajax({
        url: "/benchmarks/submit",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            let title;
            markAllStagesAsComplete();
            if(response.status === "success"){
                showReloadModal("Benchmark Successfully Registered");
                timer(3, url="/benchmarks/ui/display/"+response.benchmark_id);
            }
            else{
                $("#errorModalLabel").html("Benchmark Registration Failed");
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    showPanel(`Registering Benchmark...`);
    getEvents(logPanel, stagesList, currentStageElement);
}

function cancelSubmitBenchmark(){
    window.location.reload(true);
}

function showSubmitBenchmark(){
    window.location.href = "/benchmarks/submit/ui";
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

function getBenchmarks(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/benchmarks/ui?mine_only="+mine_only;
}

function mlcubesConfirm(element){
    const confirmBtn = document.getElementById("approve-reject");
    const benchmark_id = element.getAttribute("data-benchmark-id");
    const mlcube_id = element.getAttribute("data-mlcubes-id");
    const dataset_id = element.getAttribute("data-datasets-id");
    const type = element.getAttribute("data-status-name");
    confirmBtn.setAttribute("onclick", `mlcubesApproveReject('${type}', ${benchmark_id}, ${mlcube_id}, ${dataset_id})`)
    if(type=="approve"){
        $("#confirmTitle").text("Approval Confirmation");
        $("#confirmText").html("Are you sure you want to approve this association?<br><span class='fs-5 text-danger fw-bold'>This action cannot be undone.</span>");
    }
    else{
        $("#confirmTitle").text("Rejection Confirmation");
        $("#confirmText").html("Are you sure you want to reject this association?<br><span class='text-danger fw-bold'>This action cannot be undone.</span>");
    }
    const modal = new bootstrap.Modal('#confirmModal', {
        keyboard: false,
        backdrop: "static"
    })
    modal.show();
}

function datasetsConfirm(element){
    const confirmBtn = document.getElementById("approve-reject");
    const benchmark_id = element.getAttribute("data-benchmark-id");
    const mlcube_id = element.getAttribute("data-mlcubes-id");
    const dataset_id = element.getAttribute("data-datasets-id");
    const type = element.getAttribute("data-status-name");
    confirmBtn.setAttribute("onclick", `mlcubesApproveReject('${type}', ${benchmark_id}, ${mlcube_id}, ${dataset_id})`)
    if(type=="approve"){
        $("#confirmTitle").text("Approval Confirmation");
        $("#confirmText").html("Are you sure you want to approve this association?<br><span class='fs-5 text-danger fw-bold'>This action cannot be undone.</span>");
    }
    else{
        $("#confirmTitle").text("Rejection Confirmation");
        $("#confirmText").html("Are you sure you want to reject this association?<br><span class='text-danger fw-bold'>This action cannot be undone.</span>");
    }
    const modal = new bootstrap.Modal('#confirmModal', {
        keyboard: false,
        backdrop: "static"
    })
    modal.show();
}

function mlcubesApproveReject(type, benchmark_id, mlcube_id, dataset_id){
    showLoading();
    const mlcubesBtns = document.querySelectorAll(".mlcubes-btn");
    const datasetsBtns = document.querySelectorAll(".datasets-btn");
    mlcubesBtns.forEach(e => {
        e.disabled = true;
    });
    datasetsBtns.forEach(e => {
        e.disabled = true;
    });
    const formData = new FormData;
    formData.append("benchmark_id", benchmark_id);
    if (mlcube_id)
        formData.append("mlcube_id", mlcube_id);
    if (dataset_id)
        formData.append("dataset_id", dataset_id);

    $.ajax({
        url: `/benchmarks/${type}`,
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            hideLoading();
            let title;
            if(response.status === "success"){
                if(type == "approve")
                    title = "Association Approved Successfully";
                else
                    title = "Association Rejected Successfully";
                showReloadModal(title);
                timer(3);
            }
            else{
                if(type == "approve")
                    title = "Failed to Approve Association";
                else
                    title = "Failed to Reject Association";
                $("#errorModalLabel").html(title);
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
}

function respond_yes(){
    $.ajax({
        url: "/events",
        type: "POST",
        data: { is_approved: true },
    });
}
function respond_no(){
    $.ajax({
        url: "/events",
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

function login(event){
    event.preventDefault();
    const formData = new FormData($("#medperf-login")[0]);
    $.ajax({
        url: "/medperf_login",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            if(response.status === "success"){
                showReloadModal("Successfully Logged In");
                timer(3, url="/");
            }
            else{
                $("#errorModalLabel").html("Login Failed");
                $("#errorText").html(response.error);
                const errorModal = new bootstrap.Modal('#errorModal', {
                    keyboard: false,
                    backdrop: "static"
                });
                errorModal.show();
            }
            
        },
        error: function(xhr, status, error) {
            console.log("Error occurred:", error);
        }
    });
    $("#medperf-login").hide();
    processLogin();
}

function processLogin(){
    $.ajax({
        url: "/events",
        type: "GET",
        dataType: "json",
        success: function(response) {
            if (response.end)
                return;
            if(response.type === "url"){
                $("#login-response").show();
                $("#link-text").show();
                document.getElementById("link").setAttribute("href", response.message);
                document.getElementById("link").innerHTML = response.message;
            }
            else if (response.type === "code"){
                $("#code-text").show();
                $("#code").html(response.message)
                $("#warning").show();
            }
            processLogin();
        },
        error: function(xhr, status, error) {
            console.log("Error getEvents");
            console.log(xhr);
            console.log(status);
            console.log(error);
        }
    });
}