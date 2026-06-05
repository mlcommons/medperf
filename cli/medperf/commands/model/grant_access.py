from medperf import config
from medperf.enums import ModelType
from medperf.commands.mlcube.grant_access import GrantAccess as GrantContainerAccess
from medperf.entities.model import Model


class GrantAccess:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        model_id: int,
        approved: bool = False,
        allowed_emails: str = None,
    ):
        model = Model.get(model_id)
        if model.type != ModelType.CONTAINER.value:
            config.ui.print_error(
                "Grant access is only applicable for container models."
            )
            return
        container_id = model.container.id
        return GrantContainerAccess.run(
            benchmark_id,
            container_id,
            approved=approved,
            allowed_emails=allowed_emails,
        )
