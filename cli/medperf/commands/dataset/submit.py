from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import approval_prompt, pretty_error, request_approval
from medperf.entities.dataset import Dataset


class DatasetRegistration:
    @staticmethod
    def run(data_uid: str, comms: Comms, ui: UI, approved=False):
        """Registers a database to the backend.

        Args:
            data_uid (str): UID Hint of the unregistered dataset
        """

        dset = Dataset(data_uid, ui)

        if dset.uid:
            pretty_error(
                "This dataset has already been registered.", ui, add_instructions=False
            )

        msg = "Do you approve the registration of the presented data to the MLCommons comms? [Y/n] "
        approved = approved or approval_prompt(msg, ui)
        dset.status = "APPROVED" if approved else "REJECTED"
        if approved:
            ui.print("Uploading...")
            dset.upload(comms)
            dset.set_registration()
        else:
            pretty_error("Registration request cancelled.", ui, add_instructions=False)
