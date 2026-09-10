from medperf import config
from medperf.account_management.account_management import get_medperf_user_object
from medperf.cc.assets import set_permitted_grants, sync_cc_metadata
from medperf.cc.workloads import get_model_grants
from medperf.entities.model import Model
from medperf.exceptions import MedperfException
from medperf_cc import AssetKind


class ModelUpdateCCPolicy:
    """Republishes which workloads may load this model's weights.

    Whatever a sync leaves out stops being able to decrypt, which is the whole
    of how a grant is taken away."""

    @classmethod
    def run(cls, model_uid: int):
        model = Model.get(model_uid)
        if model.owner != get_medperf_user_object().id:
            raise MedperfException("User must be model owner")
        if not model.is_cc_configured():
            raise MedperfException(
                f"Model {model.id} is not configured for confidential computing."
            )
        with config.ui.interactive():
            config.ui.text = "Updating model confidential computing policy"
            grants = get_model_grants(model)
            set_permitted_grants(model, AssetKind.MODEL, grants)
            sync_cc_metadata(model, config.comms.update_model)
