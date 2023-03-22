from medperf.exceptions import InvalidArgumentError
from tabulate import tabulate

from medperf import config


class EntityList:
    @staticmethod
    def run(
        entity_class, fields, comms_func: callable = None, local_only: bool = False
    ):
        """Lists all local datasets

        Args:
            local_only (bool, optional): Display all local results. Defaults to False.
            mine_only (bool, optional): Display all current-user results. Defaults to False.
        """
        entity_list = EntityList(entity_class, fields, comms_func, local_only)
        entity_list.prepare()
        entity_list.validate()
        entity_list.filter()
        entity_list.display()

    def __init__(self, entity_class, fields, comms_func, local_only):
        self.entity_class = entity_class
        self.fields = fields
        self.comms_func = comms_func
        self.local_only = local_only
        self.data = []

    def prepare(self):
        entities = self.entity_class.all(
            local_only=self.local_only, comms_func=self.comms_func
        )
        self.data = [entity.display_dict() for entity in entities]

    def validate(self):
        if self.data:
            valid_fields = set(self.data[0].keys())
            chosen_fields = set(self.fields)
            if not chosen_fields.issubset(valid_fields):
                invalid_fields = chosen_fields.difference(valid_fields)
                invalid_fields = ", ".join(invalid_fields)
                raise InvalidArgumentError(f"Invalid field(s): {invalid_fields}")

    def filter(self):
        self.data = [
            {field: entity_dict[field] for field in self.fields}
            for entity_dict in self.data
        ]

    def display(self):
        headers = self.fields
        data_lists = [list(entity_dict.values()) for entity_dict in self.data]
        tab = tabulate(data_lists, headers=headers)
        config.ui.print(tab)
