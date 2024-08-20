from typing import List, Type
from medperf.entities.interface import Entity
from medperf.exceptions import InvalidArgumentError
from tabulate import tabulate

from medperf import config
from medperf.account_management import get_medperf_user_data


class EntityList:
    @staticmethod
    def run(
        entity_class: Type[Entity],
        fields: List[str],
        unregistered: bool = False,
        mine_only: bool = False,
        **kwargs,
    ):
        """Lists all local datasets

        Args:
            unregistered (bool, optional): Display only local unregistered results. Defaults to False.
            mine_only (bool, optional): Display all registered current-user results. Defaults to False.
            kwargs (dict): Additional parameters for filtering entity lists.
        """
        entity_list = EntityList(
            entity_class, fields, unregistered, mine_only, **kwargs
        )
        entity_list.prepare()
        entity_list.validate()
        entity_list.filter()
        entity_list.display()

    def __init__(
        self,
        entity_class: Type[Entity],
        fields: List[str],
        unregistered: bool,
        mine_only: bool,
        **kwargs,
    ):
        self.entity_class = entity_class
        self.fields = fields
        self.unregistered = unregistered
        self.mine_only = mine_only
        self.filters = kwargs
        self.data = []

    def prepare(self):
        if self.mine_only:
            self.filters["owner"] = get_medperf_user_data()["id"]

        entities = self.entity_class.all(
            unregistered=self.unregistered, filters=self.filters
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
