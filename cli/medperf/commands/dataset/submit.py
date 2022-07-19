from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import pretty_error
from medperf.entities.dataset import Dataset


class DatasetRegistration:
    @staticmethod
    def run(data_uid: str, comms: Comms, ui: UI):
        """Registers a database to the backend.

        Args:
            data_uid (str): UID Hint of the unregistered dataset
        """

        dset = Dataset(data_uid, ui)

        if dset.uid:
            pretty_error(
                "This dataset has already been registered.", ui, add_instructions=False
            )

        if dset.request_registration_approval(ui):
            ui.print("Uploading...")
            dset.upload(comms)
            dset.set_registration()
