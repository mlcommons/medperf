import medperf.config as config
from medperf.entities.aggregator import Aggregator
from medperf.utils import remove_path


class SubmitAggregator:
    @classmethod
    def run(cls, name, address, port):
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
        submission = cls(name, address, port)

        with ui.interactive():
            ui.text = "Submitting Aggregator to MedPerf"
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        submission.write(updated_benchmark_body)

    def __init__(self, name, address, port):
        self.ui = config.ui
        # TODO: server config should be a URL...
        server_config = {
            "address": address,
            "agg_addr": address,
            "port": port,
            "agg_port": port,
        }
        self.aggregator = Aggregator(name=name, server_config=server_config)
        config.tmp_paths.append(self.aggregator.path)

    def submit(self):
        updated_body = self.aggregator.upload()
        return updated_body

    def write(self, updated_body):
        remove_path(self.aggregator.path)
        aggregator = Aggregator(**updated_body)
        aggregator.write()
