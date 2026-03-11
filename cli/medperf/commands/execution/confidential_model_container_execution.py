import base64

from medperf.asset_management.gcp_utils import CCWorkloadID
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.certificate import Certificate
import medperf.config as config
from medperf.exceptions import DecryptionError, ExecutionError

from medperf.account_management import get_medperf_user_object
from medperf.asset_management.asset_management import (
    run_workload,
    download_results,
    workload_results_exists,
)
from medperf.utils import get_string_hash
from medperf.commands.certificate.utils import load_user_private_key
from medperf.commands.execution.container_execution import ContainerExecution


class ConfidentialModelContainerExecution:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        dataset: Dataset,
        model: Model,
        script: Cube,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution_flow = cls(
            benchmark_id,
            dataset,
            model,
            script,
            evaluator,
            execution,
            ignore_model_errors,
        )
        execution_flow.setup_local_environment()
        with config.ui.interactive():
            execution_flow.get_operator()
            execution_flow.validate()
            execution_flow.prepare()
            execution_flow.setup_workload()
            if execution_flow.should_run_workload():
                execution_flow.run_workload()
            execution_flow.download_predictions()
            execution_flow.run_evaluation()
        execution_summary = execution_flow.todict()
        return execution_summary

    def __init__(
        self,
        benchmark_id: int,
        dataset: Dataset,
        model: Model,
        script: Cube,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.benchmark_id = benchmark_id
        self.dataset = dataset
        self.model = model
        self.script = script
        self.evaluator = evaluator
        self.execution = execution
        self.ignore_model_errors = ignore_model_errors
        self.operator = None
        self.dataset_cc_config = None
        self.model_cc_config = None
        self.operator_cc_config = None
        self.local_execution_flow = None

    def setup_local_environment(self):
        self.local_execution_flow = ContainerExecution(
            self.dataset,
            self.model,
            self.evaluator,
            self.execution,
            self.ignore_model_errors,
        )
        self.local_execution_flow.prepare()

    def get_operator(self):
        self.operator = get_medperf_user_object()

    def validate(self):
        if not self.dataset.is_cc_configured():
            raise ExecutionError(
                f"Dataset {self.dataset.id} is not configured for confidential computing."
            )
        if not self.model.is_cc_configured():
            raise ExecutionError(
                f"Model {self.model.id} is not configured for confidential computing."
            )
        if not self.operator.is_cc_configured():
            raise ExecutionError(
                "User does not have a configuration to operate a confidential execution."
            )

    def prepare(self):
        self.dataset_cc_config = self.dataset.get_cc_config()
        self.model_cc_config = self.model.get_cc_config()
        self.operator_cc_config = self.operator.get_cc_config()
        self.asset = self.model.asset_obj

    def setup_workload(self):
        if self.dataset.owner == self.operator.id:
            cert_obj = Certificate.get_user_certificate()
        else:
            datasets_certs = config.comms.get_benchmark_datasets_certificates(
                self.benchmark_id
            )
            for cert in datasets_certs:
                if cert["owner"]["id"] == self.dataset.owner:
                    cert.pop("owner")
                    cert_obj = Certificate(**cert)
                    break
            else:
                raise ExecutionError("Dataset not associated.")

        public_key_bytes = cert_obj.public_key()
        result_collector_public_key = base64.b64encode(public_key_bytes)
        workload = CCWorkloadID(
            data_hash=self.dataset.generated_uid,
            model_hash=self.asset.asset_hash,
            script_hash=self.script.image_hash,
            result_collector_hash=get_string_hash(result_collector_public_key),
            data_id=self.dataset.id,
            model_id=self.asset.id,
            script_id=self.script.id,
            execution_id=self.execution.id,
        )

        self.workload = workload
        self.result_collector_public_key = result_collector_public_key

    def should_run_workload(self):
        return not workload_results_exists(self.operator_cc_config, self.workload)

    def run_workload(self):
        config.ui.text = "Running CC workload..."
        docker_image = self.script.parser.get_setup_args()
        # TODO: docker.io/
        docker_image = "docker.io/" + docker_image
        run_workload(
            docker_image,
            self.workload,
            self.dataset_cc_config,
            self.model_cc_config,
            self.operator_cc_config,
            self.result_collector_public_key.decode("utf-8"),
        )

    def download_predictions(self):
        config.ui.text = "Downloading results..."
        results_path = self.local_execution_flow.preds_path
        private_key_bytes = load_user_private_key()
        if private_key_bytes is None:
            raise DecryptionError("Missing Private Key")

        # TODO: results_path may contain root name
        download_results(
            self.operator_cc_config, self.workload, private_key_bytes, results_path
        )

    def run_evaluation(self):
        return self.local_execution_flow.run_evaluation()

    def todict(self):
        return self.local_execution_flow.todict()
