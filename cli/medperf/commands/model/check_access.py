from medperf import config
from medperf.enums import ModelType
from medperf.commands.mlcube.check_access import CheckAccess as CheckContainerAccess
from medperf.entities.model import Model


class CheckAccess:
    @classmethod
    def run(cls, model_id):
        model = Model.get(model_id)
        if model.type != ModelType.CONTAINER.value:
            config.ui.print_error(
                "Access check is only applicable for container models."
            )
            return
        container_id = model.container.id
        return CheckContainerAccess.run(container_id)
