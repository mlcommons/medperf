
function onBenchmarkRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal("Benchmark Successfully Registered");
        timer(3, "/benchmarks/ui/display/"+response.benchmark_id);
    }
    else{
        showErrorModal("Benchmark Registration Failed", response);
    }
}

async function registerBenchmark(registerButton){
    addSpinner(registerButton);

    const formData = new FormData($("#benchmark-register-form")[0]);

    disableElements("#benchmark-register-form input, #benchmark-register-form textarea, #benchmark-register-form select, #benchmark-register-form button");

    ajaxRequest(
        "/benchmarks/register",
        "POST",
        formData,
        onBenchmarkRegisterSuccess,
        "Error registering benchmark:"
    )

    showPanel(`Registering Benchmark...`);
    window.runningTaskId = await getTaskId();
    streamEvents(logPanel, stagesList, currentStageElement);
}

function checkBenchmarkFormValidity() {
    const nameValue = $("#name").val().trim();
    const descriptionValue = $("#description").val().trim();
    const referenceDatasetTarballUrlValue = $("#reference-dataset-tarball-url").val().trim();

    var dataPreparationContainerValue = $("#data-preparation-container").val();
    var referenceModelContainerValue = $("#reference-model-container").val();
    var evaluatorContainerValue = $("#evaluator-container").val();

    dataPreparationContainerValue = dataPreparationContainerValue ? Number(dataPreparationContainerValue) : 0;
    referenceModelContainerValue = referenceModelContainerValue ? Number(referenceModelContainerValue) : 0;
    evaluatorContainerValue = evaluatorContainerValue ? Number(evaluatorContainerValue) : 0;

    const isValid = Boolean(
        nameValue.length > 0 &&
        descriptionValue.length > 0 &&
        referenceDatasetTarballUrlValue.length > 0 &&
        dataPreparationContainerValue > 0 &&
        referenceModelContainerValue > 0 &&
        evaluatorContainerValue > 0
    );
    $("#register-benchmark-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-benchmark-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerBenchmark, "register this benchmark?");
    });

    $("#benchmark-register-form input, #benchmark-register-form textarea, #benchmark-register-form select").on("keyup change", checkBenchmarkFormValidity);
});