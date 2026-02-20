import base64
import logging

from medperf.entities.asset import Asset
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.certificate import Certificate
import medperf.config as config
from medperf.exceptions import ExecutionError, CommunicationError

from medperf.account_management import get_medperf_user_object
from medperf.asset_management.asset_management import run_workload
from medperf.utils import get_string_hash


class ConfidentialExecution:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        dataset: Dataset,
        model: Model,
        script: Cube,
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
            benchmark_id, dataset, model, script, execution, ignore_model_errors
        )
        execution_flow.get_operator()
        execution_flow.validate()
        execution_flow.prepare()
        execution_flow.set_pending_status()
        execution_flow.run_workload()
        execution_summary = execution_flow.todict()
        return execution_summary

    def __init__(
        self,
        benchmark_id: int,
        dataset: Dataset,
        model: Model,
        script: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.benchmark_id = benchmark_id
        self.dataset = dataset
        self.model = model
        self.script = script
        self.execution = execution
        self.ignore_model_errors = ignore_model_errors
        self.operator = None
        self.dataset_cc_config = None
        self.model_cc_config = None
        self.operator_cc_config = None

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
        self.asset = Asset.get(self.model.asset)

    def set_pending_status(self):
        self.__send_report("pending")

    def run_workload(self):
        docker_image = self.script.parser.get_setup_args()
        datasets_certs = config.comms.get_benchmark_datasets_certificates(
            self.benchmark_id
        )
        for cert in datasets_certs:
            if cert["owner"]["id"] == self.dataset.owner:
                cert.pop("owner")
                cert_obj = Certificate(**cert)
                public_key_bytes = cert_obj.public_key()
                result_collector_public_key = base64.b64encode(public_key_bytes)
                break
        else:
            raise ExecutionError("Dataset not associated.")

        workload_dict = {
            "image_digest": self.script.image_hash,
            "EXPECTED_DATA_HASH": self.dataset.generated_uid,
            "EXPECTED_MODEL_HASH": self.asset.asset_hash,
            "EXPECTED_RESULT_COLLECTOR_HASH": get_string_hash(
                result_collector_public_key
            ),
        }
        run_workload(
            docker_image,
            workload_dict,
            self.dataset_cc_config,
            self.model_cc_config,
            self.operator_cc_config,
            result_collector_public_key.decode("utf-8"),
        )

    def todict(self):
        return {
            "results": {},
            "partial": False,
        }

    def __send_report(self, status: str):
        if self.execution is None or self.execution.id is None:
            return

        execution_id = self.execution.id
        body = {"script_report": {"execution_status": status}}
        try:
            config.comms.update_execution(execution_id, body)
        except CommunicationError as e:
            logging.error(str(e))
            return
