import os

from medperf.config import config
from medperf.entities import Result, Dataset
from medperf.utils import pretty_error


class ResultSubmission:
    def __init__(self, benchamrk_uid, data_uid, model_uid, comms, ui):
        self.benchmark_uid = benchamrk_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui

    @classmethod
    def run(cls, benchmark_uid, data_uid, model_uid, comms, ui):
        dset = Dataset(data_uid, ui)
        sub = cls(benchmark_uid, dset.generated_uid, model_uid, comms, ui)
        sub.upload_results()

    def upload_results(self):
        out_path = self.__results_path()
        result = Result(out_path, self.benchmark_uid, self.data_uid, self.model_uid)
        approved = result.request_approval(self.ui)
        if not approved:
            msg = "Results upload operation cancelled"
            pretty_error(msg, self.ui, add_instructions=False)

        result.upload(self.comms)

    def __results_path(self):
        out_path = config["results_storage"]
        bmark_uid = str(self.benchmark_uid)
        model_uid = str(self.model_uid)
        data_uid = str(self.data_uid)
        out_path = os.path.join(out_path, bmark_uid, model_uid, data_uid)
        out_path = os.path.join(out_path, "results.yaml")
        return out_path
