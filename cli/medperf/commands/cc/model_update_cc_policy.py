from medperf.entities.model import Model
from medperf.exceptions import MedperfException
from medperf.asset_management.asset_management import update_model_cc_policy


class ModelUpdateCCPolicy:
    @classmethod
    def run(cls, model_uid: int):
        model = Model.get(model_uid)
        if not model.is_cc_configured():
            raise MedperfException(
                f"Model {model.id} is not configured for confidential computing."
            )
        policy = {}
        update_model_cc_policy(model, policy)
