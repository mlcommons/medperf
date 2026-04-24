import medperf.config as config
from medperf.entities.ca import CA
from medperf.utils import remove_path
from medperf.entities.cube import Cube


class SubmitCA:
    @classmethod
    def run(
        cls,
        name: str,
        config_path: str,
        ca_mlcube: int,
        client_mlcube: int,
        server_mlcube: int,
    ):
        """Submits a new ca to the medperf platform
        Args:
            name (str): ca name
            config_path (dict): ca config
            ca_mlcube (int): ca_mlcube mlcube uid
            client_mlcube (int): client_mlcube mlcube uid
            server_mlcube (int): server_mlcube mlcube uid
        """
        ui = config.ui
        submission = cls(name, config_path, ca_mlcube, client_mlcube, server_mlcube)

        with ui.interactive():
            ui.text = "Submitting CA to MedPerf"
            submission.validate_ca_cubes()
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        submission.write(updated_benchmark_body)

    def __init__(
        self,
        name: str,
        config_path: str,
        ca_mlcube: int,
        client_mlcube: int,
        server_mlcube: int,
    ):
        self.ui = config.ui
        self.ca = CA(
            name=name,
            config=config_path,
            ca_mlcube=ca_mlcube,
            client_mlcube=client_mlcube,
            server_mlcube=server_mlcube,
        )
        config.tmp_paths.append(self.ca.path)

    def validate_ca_cubes(self):
        Cube.get(self.ca.ca_mlcube)
        Cube.get(self.ca.client_mlcube)
        Cube.get(self.ca.server_mlcube)

    def submit(self):
        updated_body = self.ca.upload()
        return updated_body

    def write(self, updated_body):
        remove_path(self.ca.path)
        ca = CA(**updated_body)
        ca.write()
