import logging
from medperf.enums import Status
import validators

import medperf.config as config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.entities.benchmark import Benchmark
from medperf.utils import get_file_sha1, generate_tmp_uid, pretty_error
from medperf.commands.compatibility_test import CompatibilityTestExecution


class SubmitBenchmark:
    @classmethod
    def run(cls, benchmark_info: dict, ui: UI = config.ui):
        """Submits a new cube to the medperf platform
        Args:
            benchmark_info (dict): benchmark information
                expected keys:
                    name (str): benchmark name
                    description (str): benchmark description
                    docs_url (str): benchmark documentation url
                    demo_url (str): benchmark demo dataset url
                    demo_hash (str): benchmark demo dataset hash
                    data_preparation_mlcube (str): benchmark data preparation mlcube uid
                    reference_model_mlcube (str): benchmark reference model mlcube uid
                    evaluator_mlcube (str): benchmark data evaluator mlcube uid
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        submission = cls(benchmark_info)
        if not submission.is_valid():
            pretty_error("Invalid benchmark information")

        with ui.interactive():
            ui.text = "Getting additional information"
            submission.get_extra_information()
            ui.print("> Completed benchmark registration information")
            ui.text = "Submitting Benchmark to MedPerf"
            submission.submit()
        ui.print("Uploaded")

    def __init__(self, benchmark_info: dict, comms: Comms = config.comms, ui: UI = config.ui):
        self.comms = comms
        self.ui = ui
        self.name = benchmark_info["name"]
        self.description = benchmark_info["description"]
        self.docs_url = benchmark_info["docs_url"]
        self.demo_url = benchmark_info["demo_url"]
        self.demo_hash = benchmark_info["demo_hash"]
        self.demo_uid = None
        self.data_preparation_mlcube = benchmark_info["data_preparation_mlcube"]
        self.reference_model_mlcube = benchmark_info["reference_model_mlcube"]
        self.data_evaluator_mlcube = benchmark_info["evaluator_mlcube"]
        self.results = None

    def is_valid(self) -> bool:
        """Validates that user-provided benchmark information is correct

        Returns:
            bool: Wether or not the benchmark information is valid
        """
        name_valid_length = 0 < len(self.name) < 20
        desc_valid_length = len(self.description) < 100
        docs_url_valid = self.docs_url == "" or validators.url(self.docs_url)
        demo_url_valid = self.demo_url == "" or validators.url(self.demo_url)
        demo_hash_if_no_url = self.demo_url or self.demo_hash
        prep_uid_valid = self.data_preparation_mlcube.isdigit()
        model_uid_valid = self.reference_model_mlcube.isdigit()
        eval_uid_valid = self.data_evaluator_mlcube.isdigit()

        valid_tests = [
            ("name", name_valid_length, "Name is invalid"),
            ("description", desc_valid_length, "Description is too long"),
            ("docs_url", docs_url_valid, "Documentation URL is invalid"),
            ("demo_url", demo_url_valid, "Demo Dataset Tarball URL is invalid"),
            (
                "demo_hash",
                demo_hash_if_no_url,
                "Demo Datset Hash must be provided if no URL passed",
            ),
            (
                "data_preparation_mlcube",
                prep_uid_valid,
                "Data Preparation MLCube UID is invalid",
            ),
            (
                "reference_model_mlcube",
                model_uid_valid,
                "Reference Model MLCube is invalid",
            ),
            (
                "data_evaluator_mlcube",
                eval_uid_valid,
                "Data Evaluator MLCube is invalid",
            ),
        ]

        valid = True
        for attr, test, error_msg in valid_tests:
            if not test:
                valid = False
                self.ui.print_error(error_msg)

        return valid

    def get_extra_information(self):
        """Retrieves information that must be populated automatically,
        like hash, generated uid and test results
        """
        tmp_uid = self.demo_hash if self.demo_hash else generate_tmp_uid()
        demo_dset_path = self.comms.get_benchmark_demo_dataset(self.demo_url, tmp_uid)
        demo_hash = get_file_sha1(demo_dset_path)
        if self.demo_hash and demo_hash != self.demo_hash:
            logging.error(
                f"Demo dataset hash mismatch: {demo_hash} != {self.demo_hash}"
            )
            pretty_error("Demo dataset hash does not match the provided hash", self.ui)
        self.demo_hash = demo_hash
        demo_uid, results = self.run_compatibility_test()
        self.demo_uid = demo_uid
        self.results = results

    def run_compatibility_test(self):
        """Runs a compatibility test to ensure elements are compatible,
        and to extract additional information required for submission
        """
        self.ui.print("Running compatibility test")
        data_prep = self.data_preparation_mlcube
        model = self.reference_model_mlcube
        evaluator = self.data_evaluator_mlcube
        demo_url = self.demo_url
        demo_hash = self.demo_hash
        benchmark = Benchmark.tmp(data_prep, model, evaluator, demo_url, demo_hash)
        _, data_uid, _, results = CompatibilityTestExecution.run(benchmark.uid)
        # Datasets generated by the compatibility test come with a prefix to identify them
        # This is not what we need for benchmark submissions, se we need to remove it
        prefix_len = len(config.test_dset_prefix)
        data_uid = data_uid[prefix_len:]

        return data_uid, results

    def todict(self):
        return {
            "name": self.name,
            "description": self.description,
            "docs_url": self.docs_url,
            "demo_dataset_tarball_url": self.demo_url,
            "demo_dataset_tarball_hash": self.demo_hash,
            "demo_dataset_generated_uid": self.demo_uid,
            "data_preparation_mlcube": int(self.data_preparation_mlcube),
            "reference_model_mlcube": int(self.reference_model_mlcube),
            "data_evaluator_mlcube": int(self.data_evaluator_mlcube),
            "state": "OPERATION",
            "is_valid": True,
            "approval_status": Status.PENDING.value,
            "metadata": {"results": self.results.todict()},
        }

    def submit(self):
        body = self.todict()
        benchmark = Benchmark(body)
        uid = benchmark.upload()
        benchmark.uid = uid
        benchmark.write()
