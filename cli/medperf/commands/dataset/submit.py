from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset
from medperf.utils import pretty_error


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
        remote_dsets = comms.get_user_datasets()
        remote_dset = [
            dset for dset in remote_dsets if dset["generated_uid"] == data_uid
        ]
        if len(remote_dset) == 1:
            dset.uid = remote_dset[0]["id"]
            dset.name = remote_dset[0]["name"]
            dset.location = remote_dset[0]["location"]
            dset.description = remote_dset[0]["description"]
            dset.set_registration()
            ui.print(f"Remote dataset {dset.name} detected. Updating local dataset.")
            return

        if dset.request_registration_approval(ui):
            ui.print("Uploading...")
            dset.upload(comms)
            dset.set_registration()
