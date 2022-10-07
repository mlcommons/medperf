from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import approval_prompt, pretty_error
from medperf.entities.dataset import Dataset
from medperf.enums import Status


class DatasetRegistration:
    @staticmethod
    def run(data_uid: str, comms: Comms, ui: UI, approved=False):
        """Registers a database to the backend.

        Args:
            data_uid (str): UID Hint of the unregistered dataset
        """

        dset = Dataset(data_uid)

        if dset.uid:
            pretty_error(
                "This dataset has already been registered.", ui, add_instructions=False
            )
        remote_dsets = comms.get_user_datasets()
        remote_dset = [
            remote_dset
            for remote_dset in remote_dsets
            if remote_dset["generated_uid"] == dset.generated_uid
        ]
        if len(remote_dset) == 1:
            dset.uid = remote_dset[0]["id"]
            dset.name = remote_dset[0]["name"]
            dset.location = remote_dset[0]["location"]
            dset.description = remote_dset[0]["description"]
            dset.set_registration()
            ui.print(f"Remote dataset {dset.name} detected. Updating local dataset.")
            return

        msg = "Do you approve the registration of the presented data to the MLCommons comms? [Y/n] "
        approved = approved or approval_prompt(msg, ui)
        dset.status = Status("APPROVED") if approved else Status("REJECTED")
        if approved:
            ui.print("Uploading...")
            dset.upload(comms)
            dset.set_registration()
        else:
            pretty_error("Registration request cancelled.", ui, add_instructions=False)
