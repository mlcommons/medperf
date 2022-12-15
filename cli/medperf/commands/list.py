from tabulate import tabulate

from medperf import config


class EntityList:
    @staticmethod
    def run(
        entity_class, fields_mapping, local_only: bool = False, mine_only: bool = False
    ):
        """Lists all local datasets

        Args:
            local_only (bool, optional): Display all local results. Defaults to False.
            mine_only (bool, optional): Display all current-user results. Defaults to False.
        """
        entity_list = EntityList(entity_class, fields_mapping, local_only, mine_only)
        entity_list.prepare()
        entity_list.filter_fields()
        entity_list.display()

    def __init__(self, entity_class, fields_mapping, local_only, mine_only):
        self.entity_class = entity_class
        self.fields_mapping = fields_mapping
        self.local_only = local_only
        self.mine_only = mine_only
        self.data = []

    def prepare(self):
        entities = self.entity_class.all(
            local_only=self.local_only, mine_only=self.mine_only
        )
        self.data = [entity.todict() for entity in entities]
        self.extra_data = [
            {"UID": entity.identifier, "Registered": entity.is_registered()}
            for entity in entities
        ]

    def filter_fields(self):
        fields = list(self.fields_mapping.values())
        self.data = [
            {field: entity_dict[field] for field in fields} for entity_dict in self.data
        ]

    def display(self):
        headers = list(self.extra_data.keys()) + list(self.fields_mapping.keys())
        data_lists = [
            list(extra_dict.values()) + list(entity_dict.values())
            for extra_dict, entity_dict in zip(self.extra_data, self.data)
        ]
        tab = tabulate(data_lists, headers=headers)
        config.ui.print(tab)
