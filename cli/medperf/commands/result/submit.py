from medperf.entities import Result, Dataset
from medperf.utils import pretty_error, results_path


class ResultSubmission:
    def __init__(self, benchmark_uid, data_uid, model_uid, comms, ui):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui

    @classmethod
    def run(cls, benchmark_uid, data_uid, model_uid, comms, ui):
        dset = Dataset(data_uid, ui)
        sub = cls(benchmark_uid, dset.uid, model_uid, comms, ui)
        sub.upload_results()

    def upload_results(self):
        out_path = results_path(self.benchmark_uid, self.model_uid, self.data_uid)
        result = Result(out_path, self.benchmark_uid, self.data_uid, self.model_uid)
        approved = result.request_approval(self.ui)
        if not approved:
            msg = "Results upload operation cancelled"
            pretty_error(msg, self.ui, add_instructions=False)

        result.upload(self.comms)
