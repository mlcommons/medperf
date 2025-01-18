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
    const dataset_name = element.getAttribute("data-dataset-name")
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