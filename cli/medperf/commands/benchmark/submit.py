import os
import shutil
import logging

import medperf.config as config
from medperf.entities.benchmark import Benchmark
from medperf.utils import get_file_sha1, generate_tmp_uid
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from medperf.exceptions import InvalidEntityError
from medperf.comms.entity_resources import resources


class SubmitBenchmark:
    @classmethod
    def run(cls, benchmark_info: dict, no_cache: bool = True):
        """Submits a new cube to the medperf platform
        Args:
            benchmark_info (dict): benchmark information
                expected keys:
                    name (str): benchmark name
                    description (str): benchmark description
                    docs_url (str): benchmark documentation url
                    demo_url (str): benchmark demo dataset url
                    demo_hash (str): benchmark demo dataset hash
                    data_preparation_mlcube (int): benchmark data preparation mlcube uid
                    reference_model_mlcube (int): benchmark reference model mlcube uid
                    evaluator_mlcube (int): benchmark data evaluator mlcube uid
        """
        ui = config.ui
        submission = cls(benchmark_info, no_cache)

        with ui.interactive():
            ui.text = "Getting additional information"
            submission.get_extra_information()
            ui.print("> Completed benchmark registration information")
            ui.text = "Submitting Benchmark to MedPerf"
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        submission.to_permanent_path(updated_benchmark_body)
        submission.write(updated_benchmark_body)

    def __init__(self, benchmark_info: dict, no_cache: bool = True):
        self.ui = config.ui
        self.bmk = Benchmark(**benchmark_info)
        self.no_cache = no_cache

    def get_extra_information(self):
        """Retrieves information that must be populated automatically,
        like hash, generated uid and test results
        """
        bmk_demo_url = self.bmk.demo_dataset_tarball_url
        bmk_demo_hash = self.bmk.demo_dataset_tarball_hash
        tmp_uid = bmk_demo_hash if bmk_demo_hash else generate_tmp_uid()
        demo_dset_path = resources.get_benchmark_demo_dataset(bmk_demo_url, tmp_uid)
        demo_hash = get_file_sha1(demo_dset_path)
        if bmk_demo_hash and demo_hash != bmk_demo_hash:
            logging.error(f"Demo dataset hash mismatch: {demo_hash} != {bmk_demo_hash}")
            raise InvalidEntityError(
                "Demo dataset hash does not match the provided hash"
            )
        self.bmk.demo_dataset_tarball_hash = demo_hash
        demo_uid, results = self.run_compatibility_test()
        self.bmk.demo_dataset_generated_uid = demo_uid
        self.bmk.metadata = {"results": results}

    def run_compatibility_test(self):
        """Runs a compatibility test to ensure elements are compatible,
        and to extract additional information required for submission
        """
        self.ui.print("Running compatibility test")
        self.bmk.write()
        config.extra_cleanup_paths.append(self.bmk.path)
        data_uid, results = CompatibilityTestExecution.run(
            benchmark=self.bmk.generated_uid, no_cache=self.no_cache
        )

        return data_uid, results

    def submit(self):
        updated_body = self.bmk.upload()
        return updated_body

    def to_permanent_path(self, bmk_dict: dict):
        """Renames the temporary benchmark submission to a permanent one

        Args:
            bmk_dict (dict): dictionary containing updated information of the submitted benchmark
        """
        old_bmk_loc = self.bmk.path
        updated_bmk = Benchmark(**bmk_dict)
        new_bmk_loc = updated_bmk.path
        if os.path.exists(new_bmk_loc):
            shutil.rmtree(new_bmk_loc)
        os.rename(old_bmk_loc, new_bmk_loc)

    def write(self, updated_body):
        bmk = Benchmark(**updated_body)
        bmk.write()
