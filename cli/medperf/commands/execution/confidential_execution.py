import base64
import logging
import os
from time import time

import yaml

from medperf.asset_management.gcp_utils import CCWorkloadID
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.certificate import Certificate
import medperf.config as config
from medperf.exceptions import DecryptionError, ExecutionError, CommunicationError

from medperf.account_management import get_medperf_user_object
from medperf.asset_management.asset_management import run_workload, download_results
from medperf.utils import get_string_hash
from medperf.commands.certificate.utils import load_user_private_key
from medperf.containers.runners.docker_utils import full_docker_image_name


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
        execution_flow.setup_workload()
        execution_flow.run_workload()
        execution_flow.download_results()
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
        self.asset = self.model.asset_obj

    def set_pending_status(self):
        self.__send_report("pending")

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
        )

        self.workload = workload
        self.result_collector_public_key = result_collector_public_key

    def run_workload(self):
        config.ui.text = "Running CC workload..."
        docker_image = self.script.parser.get_setup_args()
        docker_image = full_docker_image_name(docker_image)
        run_workload(
            docker_image,
            self.workload,
            self.dataset_cc_config,
            self.model_cc_config,
            self.operator_cc_config,
            self.result_collector_public_key.decode("utf-8"),
        )

    def download_results(self):
        config.ui.text = "Downloading results..."
        timestamp = str(time()).replace(".", "_")
        results_path = os.path.join(
            config.script_result_folder, str(self.execution.id), timestamp
        )
        private_key_bytes = load_user_private_key()
        if private_key_bytes is None:
            raise DecryptionError("Missing Private Key")

        download_results(
            self.operator_cc_config, self.workload, private_key_bytes, results_path
        )

        results_file = os.path.join(results_path, "results", "results.yaml")
        if os.path.exists(results_file):
            with open(results_file, "r") as f:
                results_content = yaml.safe_load(f)
            self.results = results_content
        else:
            self.results = {}

    def todict(self):
        return {
            "results": self.results,
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
