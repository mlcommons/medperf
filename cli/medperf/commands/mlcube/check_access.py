from medperf import config
from medperf.commands.mlcube.utils import check_access_to_container


class CheckAccess:
    @classmethod
    def run(cls, model_id):
        access_dict = check_access_to_container(model_id)
        if access_dict["has_access"]:
            msg = "You are authorized: " + access_dict["reason"]
            config.ui.print(msg)
        else:
            msg = "Access denied:\n" + access_dict["reason"]
            config.ui.print_error(msg)
