
function onBenchmarkRegisterSuccess(response){
    markAllStagesAsComplete();
    if(response.status === "success"){
        showReloadModal({
            title: "Benchmark Successfully Registered",
            seconds: 3,
            url: "/benchmarks/ui/display/"+response.benchmark_id
        });
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
    const skipTestsValue = $("input[name='skip_compatibility_tests']:checked").val();

    var dataPreparationContainerValue = $("#data-preparation-container").val();
    var referenceModelValue = $("#reference-model").val();
    var evaluatorContainerValue = $("#evaluator-container").val();

    dataPreparationContainerValue = dataPreparationContainerValue ? Number(dataPreparationContainerValue) : 0;
    referenceModelValue = referenceModelValue ? Number(referenceModelValue) : 0;
    evaluatorContainerValue = evaluatorContainerValue ? Number(evaluatorContainerValue) : 0;

    const isValid = Boolean(
        nameValue.length > 0 &&
        descriptionValue.length > 0 &&
        (skipTestsValue === "true" ? skipTestsValue === "true" : referenceDatasetTarballUrlValue.length > 0) &&
        dataPreparationContainerValue > 0 &&
        referenceModelValue > 0 &&
        evaluatorContainerValue > 0
    );
    $("#register-benchmark-btn").prop("disabled", !isValid);
}

$(document).ready(() => {
    $("#register-benchmark-btn").on("click", (e) => {
        showConfirmModal(e.currentTarget, registerBenchmark, "register this benchmark?");
    });

    $("#benchmark-register-form input, #benchmark-register-form textarea, #benchmark-register-form select").on("keyup change", checkBenchmarkFormValidity);

    $("input[name='skip_compatibility_tests']").on("change", () => {
        if($("#skip-tests").is(":checked")){
            $("#demo-dataset-input-container").hide();
            $("#reference-dataset-tarball-url").val("");
        }
        else{
            $("#demo-dataset-input-container").show();
        }
    });
});