import medperf.config as config
from medperf.entities.aggregator import Aggregator
from medperf.utils import remove_path
from medperf.entities.cube import Cube


class SubmitAggregator:
    @classmethod
    def run(cls, name: str, address: str, port: int, aggregation_mlcube: int):
        """Submits a new aggregator to the medperf platform
        Args:
            name (str): aggregator name
            address (str): aggregator address/domain
            port (int): port which the aggregator will use
            aggregation_mlcube (int): aggregation mlcube uid
        """
        ui = config.ui
        submission = cls(name, address, port, aggregation_mlcube)

        with ui.interactive():
            ui.text = "Submitting Aggregator to MedPerf"
            submission.validate_agg_cube()
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        submission.write(updated_benchmark_body)

    def __init__(self, name: str, address: str, port: int, aggregation_mlcube: int):
        self.ui = config.ui
        agg_config = {"address": address, "port": port}
        self.aggregator = Aggregator(
            name=name, config=agg_config, aggregation_mlcube=aggregation_mlcube
        )
        config.tmp_paths.append(self.aggregator.path)

    def validate_agg_cube(self):
        Cube.get(self.aggregator.aggregation_mlcube)

    def submit(self):
        updated_body = self.aggregator.upload()
        return updated_body

    def write(self, updated_body):
        remove_path(self.aggregator.path)
        aggregator = Aggregator(**updated_body)
        aggregator.write()
