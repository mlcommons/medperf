from medperf import config
from medperf.enums import ModelType
from medperf.commands.mlcube.delete_keys import DeleteKeys as DeleteContainerKeys
from medperf.entities.model import Model


class DeleteKeys:
    @classmethod
    def run(cls, model_id, approved=False):
        model = Model.get(model_id)
        if model.type != ModelType.CONTAINER.value:
            config.ui.print_error(
                "Delete keys is only applicable for container models."
            )
            return
        container_id = model.container.id
        return DeleteContainerKeys.run(container_id, approved=approved)
