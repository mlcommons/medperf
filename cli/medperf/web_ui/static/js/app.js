let currentStageElement, datasetId, logPanel, stagesList;
let task_id;
let prompt_received = false;

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

async function submitResult(element){
    const buttons = document.querySelectorAll(".card button");
    buttons.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const result_name = element.getAttribute("data-result-name");
    $.ajax({
        url: "/datasets/submit_result",
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
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

async function runBenchmark(element, benchmark_id=null, dataset_id=null, model_ids=null, dataset_name=null){
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
    const select_elements = document.querySelectorAll(".card select");
    select_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const buttons = document.querySelectorAll(".card button");
    buttons.forEach(element => {
        element.setAttribute("disabled", true);
    });
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function associate(dataset_id, benchmark_id, dataset_name){
    document.getElementById("dropdown-div").classList.remove("show");
    const associate_btn = document.getElementById("associate-dropdown");
    associate_btn.setAttribute("disabled", true);
    associate_btn.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Requesting Association
    `;
    const buttons = document.querySelectorAll(".card button");
    buttons.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/datasets/associate",
        type: "POST",
        data: { dataset_id: dataset_id, benchmark_id: benchmark_id },
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
    showPanel(`Requesting Association...`);
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function setOperation(element){
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function prepare(element) {
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
    task_id = await getTaskId();
    showPanel(`Preparing Dataset...`);
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function registerDataset(element){
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Registering
    `;
    const formData = new FormData($("#dataset-form")[0]);

    const input_elements = document.querySelectorAll("#dataset-form input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const select_elements = document.querySelectorAll("#dataset-form select");
    select_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const buttons = document.querySelectorAll("#dataset-form button");
    buttons.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const textareas = document.querySelectorAll("#dataset-form textarea");
    textareas.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/datasets/register",
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
            console.error("📦 Response Text:", xhr.responseText);
        }
    });
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
    $("#respond-no").on("click", respond_no);
    $("#respond-yes").on("click", respond_yes);
}

async function testContainer(){
    const runBtn = $("#run-test");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Running
    `);
    const formData = new FormData($("#container-form")[0]);
    const input_elements = document.querySelectorAll("#container-form input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const select_elements = document.querySelectorAll("#container-form select");
    select_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/containers/test",
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
    task_id = await getTaskId()
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

function checkInput() {
    // Get elements
    const benchmark = document.getElementById("benchmark");
    const formFilePath = document.getElementById("container_path");
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

async function registerContainer(){
    const runBtn = $("#register-btn");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Registering
    `);
    const formData = new FormData($("#register-form")[0]);
    const input_elements = document.querySelectorAll("#register-form input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/containers/register",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        async: true,
        success: function(response) {
            markAllStagesAsComplete();
            if(response.status === "success"){
                showReloadModal("Model Registered Successfully");
                timer(3, url="/containers/ui/display/"+response.container_id);
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

function checkRegister(){
    // Get elements
    const name = document.getElementById("name");
    const container = document.getElementById("container_file");
    const registerBtn = document.getElementById("register-btn");
    
    // Ensure values are being retrieved
    const containerValue = container ? container.value.trim() : "";
    const nameValue = name ? name.value.trim() : "";
  
    // Validate inputs
    const isContainerValid = containerValue.length > 0 && containerValue.endsWith(".yaml");
    const isNameValid = nameValue.length > 0;

    // Enable/disable button
    registerBtn.disabled = !(isContainerValid && isNameValid);
}

function checkRegisterBenchmark(){
    // Get elements
    const name = document.getElementById("name");
    const description = document.getElementById("description");
    const reference_dataset_tarball_url = document.getElementById("reference_dataset_tarball_url");
    const data_preparation_container = document.getElementById("data_preparation_container");
    const reference_model_container = document.getElementById("reference_model_container");
    const evaluator_container = document.getElementById("evaluator_container");
    const registerBtn = document.getElementById("register-btn");
    
    // Ensure values are being retrieved
    const nameValue = name ? name.value.trim() : "";
    const descriptionValue = description ? description.value.trim() : "";
    const referenceDatasetTarballUrlValue = reference_dataset_tarball_url ? reference_dataset_tarball_url.value.trim() : "";
    const dataPreparationContainerValue = data_preparation_container ? Number(data_preparation_container.value.trim()) : 0;
    const referenceModelContainerValue = reference_model_container ? Number(reference_model_container.value.trim()) : 0;
    const evaluatorContainerValue = evaluator_container ? Number(evaluator_container.value.trim()) : 0;
  
    // Validate inputs
    const isNameValid = nameValue.length > 0;
    const isDescriptionValid = descriptionValue.length > 0;
    const isReferenceUrlValid = referenceDatasetTarballUrlValue.length > 0 && referenceDatasetTarballUrlValue.endsWith(".tar.gz");
    const isDataPreparationContainerValid = dataPreparationContainerValue > 0;
    const isReferenceModelContainerValid = referenceModelContainerValue > 0;
    const isEvaluatorContainerValid = evaluatorContainerValue > 0;
  
    // Enable/disable button
    registerBtn.disabled = !(
        isNameValid && isDescriptionValid && isReferenceUrlValid && isDataPreparationContainerValid && isReferenceModelContainerValid && isEvaluatorContainerValid
    );
}

function cancelRegister(){
    window.location.reload(true);
}

function showRegister(){
    window.location.href = "/containers/register/ui";
}

async function associateContainer(container_id, benchmark_id, contianer_name){
    document.getElementById("dropdown-div").classList.remove("show");
    const associate_btn = document.getElementById("associate-dropdown");
    associate_btn.setAttribute("disabled", true);
    associate_btn.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    Requesting Association
    `;
    $.ajax({
        url: "/containers/associate",
        type: "POST",
        data: { container_id: container_id, benchmark_id: benchmark_id },
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function testBenchmark(){
    const runBtn = $("#run-test");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Running
    `);
    const formData = new FormData($("#test-form")[0]);
    const input_elements = document.querySelectorAll("#test-form input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const textareas = document.querySelectorAll("#test-form textarea");
    textareas.forEach(element => {
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

async function registerBenchmark(){
    const runBtn = $("#register-btn");
    runBtn.prop("disabled", true);
    runBtn.html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Registering
    `);
    const formData = new FormData($("#register-form")[0]);
    const input_elements = document.querySelectorAll("#register-form input");
    input_elements.forEach(element => {
        element.setAttribute("disabled", true);
    });
    const textareas = document.querySelectorAll("#register-form textarea");
    textareas.forEach(element => {
        element.setAttribute("disabled", true);
    });
    $.ajax({
        url: "/benchmarks/register",
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
    task_id = await getTaskId();
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

function cancelRegisterBenchmark(){
    window.location.reload(true);
}

function showRegisterBenchmark(){
    window.location.href = "/benchmarks/register/ui";
}

function cleanPanel(){
    $("#panel").hide();
    $("#panel-title").html("");
    $("#stages-list").html("");
    $("#log-panel").html("");
}

function getContainers(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/containers/ui?mine_only="+mine_only;
}

function getDatasets(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/datasets/ui?mine_only="+mine_only;
}

function getBenchmarks(){
    const mine_only = $("#switch").prop("checked");
    window.location.href = "/benchmarks/ui?mine_only="+mine_only;
}

function containersConfirm(element){
    const confirmBtn = document.getElementById("approve-reject");
    const benchmark_id = element.getAttribute("data-benchmark-id");
    const container_id = element.getAttribute("data-containers-id");
    const dataset_id = element.getAttribute("data-datasets-id");
    const type = element.getAttribute("data-status-name");
    confirmBtn.setAttribute("onclick", `containersApproveReject('${type}', ${benchmark_id}, ${container_id}, ${dataset_id})`)
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
    const container_id = element.getAttribute("data-containers-id");
    const dataset_id = element.getAttribute("data-datasets-id");
    const type = element.getAttribute("data-status-name");
    confirmBtn.setAttribute("onclick", `containersApproveReject('${type}', ${benchmark_id}, ${container_id}, ${dataset_id})`)
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

function containersApproveReject(type, benchmark_id, container_id, dataset_id){
    showLoading();
    const containersBtns = document.querySelectorAll(".containers-btn");
    const datasetsBtns = document.querySelectorAll(".datasets-btn");
    containersBtns.forEach(e => {
        e.disabled = true;
    });
    datasetsBtns.forEach(e => {
        e.disabled = true;
    });
    const formData = new FormData;
    formData.append("benchmark_id", benchmark_id);
    if (container_id)
        formData.append("container_id", container_id);
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
    prompt_received = false;
    getEvents(logPanel, stagesList, currentStageElement, task_id);
}

function respond_no(){
    $.ajax({
        url: "/events",
        type: "POST",
        data: { is_approved: false },
    });
    prompt_received = false;
    getEvents(logPanel, stagesList, currentStageElement, task_id);
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
        incrementNotificationCount();
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
                    incrementNotificationCount(false);
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

function incrementNotificationCount(inc=true){
    const notification_count_element = $("#notifications-count");
    var notification_count = Number(notification_count_element.text());
    if (inc)
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

function deleteNotification(notification_id){
    const element = document.querySelector(`.dropdown-item[data-id="${notification_id}"]`);
    if(element){
        element.remove();
        if(element.getAttribute("data-read") == "false")
            incrementNotificationCount(false);
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

function getTaskId(){
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "/current_task",
            method: "get",
            success: function (response) {
                resolve(response.task_id);
            },
            error: function (xhr, status, error) {
                console.error("Failed to get task id:", error);
                reject(error);
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    notifications.forEach(notification => {
        addNotification(notification);
    });
});