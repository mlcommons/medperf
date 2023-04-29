import os
import shutil

from medperf.utils import approval_prompt, dict_pretty_print
from medperf.entities.dataset import Dataset
from medperf.enums import Status
from medperf import config
from medperf.exceptions import InvalidArgumentError


class DatasetRegistration:
    @staticmethod
    def run(data_uid: str, approved=False):
        """Registers a database to the backend.

        Args:
            data_uid (str): UID Hint of the unregistered dataset
        """
        comms = config.comms
        ui = config.ui
        dset = Dataset.get(data_uid)

        if dset.id is not None:
            # TODO: should get_dataset and update locally. solves existing issue?
            raise InvalidArgumentError("This dataset has already been registered")
        remote_dsets = comms.get_user_datasets()
        remote_dset = [
            remote_dset
            for remote_dset in remote_dsets
            if remote_dset["generated_uid"] == dset.generated_uid
        ]
        if len(remote_dset) == 1:
            dset = Dataset(**remote_dset[0])
            dset.write()
            ui.print(f"Remote dataset {dset.name} detected. Updating local dataset.")
            return dset.id

        dict_pretty_print(dset.todict())
        msg = "Do you approve the registration of the presented data to the MLCommons comms? [Y/n] "
        approved = approved or approval_prompt(msg)
        dset.status = Status("APPROVED") if approved else Status("REJECTED")
        if approved:
            ui.print("Uploading...")
            updated_dset_dict = dset.upload()
            updated_dset = Dataset(**updated_dset_dict)

            old_dset_loc = dset.path
            new_dset_loc = updated_dset.path
            if os.path.exists(new_dset_loc):
                shutil.rmtree(new_dset_loc)
            os.rename(old_dset_loc, new_dset_loc)

            updated_dset.write()
            return updated_dset.id
        else:
            ui.print("Registration request cancelled.")
