from medperf.entities.schemas import UserSchema
from medperf.entities.utils import handle_validation_error


class CCRoleSettings:
    """One confidential-computing role's settings on a user.

    Operating a workload and receiving its results are separate roles, and a
    user may hold either without the other: the results are written to whoever
    they are for, who need not be whoever ran the machine. So each role is
    configured, verified and reported on separately, and this is the same four
    questions asked of whichever one you name.
    """

    def __init__(self, metadata: dict, role: str):
        self._metadata = metadata
        self._role = role

    @property
    def config(self) -> dict:
        return self.__cc_values().get(self._role, {})

    @property
    def configured(self) -> bool:
        return self.config != {}

    @property
    def initialized(self) -> bool:
        return self.__cc_values().get(f"{self._role}_initialized", False)

    def set(self, config: dict) -> None:
        cc_values = self._metadata.setdefault("cc", {})
        cc_values[self._role] = config
        cc_values[f"{self._role}_initialized"] = False

    def mark_initialized(self) -> None:
        if not self.configured:
            return
        self._metadata.setdefault("cc", {})[f"{self._role}_initialized"] = True

    def __cc_values(self) -> dict:
        return self._metadata.get("cc", {})


class User:
    """
    Class representing a User

    """

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = UserSchema(**kwargs)
        self._fields = list(self._model.__fields__.keys())
        self.id = self._model.id
        self.username = self._model.username
        self.email = self._model.email
        self.first_name = self._model.first_name
        self.last_name = self._model.last_name
        self.metadata = self._model.metadata

    def __setattr__(self, name, value):
        if (
            hasattr(self, "_model")
            and hasattr(self, "_fields")
            and name in self._fields
        ):
            setattr(self._model, name, value)
        super().__setattr__(name, value)

    @property
    def cc_operator(self) -> CCRoleSettings:
        """How this user runs confidential workloads. Theirs alone."""
        return CCRoleSettings(self.metadata, "operator")

    @property
    def cc_collector(self) -> CCRoleSettings:
        """Where this user receives results.

        Read by whoever operates an execution collecting for them, so it holds
        an address and no credentials -- the collector's own storage
        credentials never leave their machine."""
        return CCRoleSettings(self.metadata, "collector")
