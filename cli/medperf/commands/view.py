import yaml
import json
from typing import Union, Type

from medperf.config_management import config
from medperf.account_management import get_medperf_user_data
from medperf.entities.interface import Entity
from medperf.exceptions import InvalidArgumentError


class EntityView:
    @staticmethod
    def run(
        entity_id: Union[int, str],
        entity_class: Type[Entity],
        format: str = "yaml",
        unregistered: bool = False,
        mine_only: bool = False,
        output: str = None,
        **kwargs,
    ):
        """Displays the contents of a single or multiple entities of a given type

        Args:
            entity_id (Union[int, str]): Entity identifies
            entity_class (Entity): Entity type
            unregistered (bool, optional): Display only local unregistered entities. Defaults to False.
            mine_only (bool, optional): Display all current-user entities. Defaults to False.
            format (str, optional): What format to use to display the contents. Valid formats: [yaml, json]. Defaults to yaml.
            output (str, optional): Path to a file for storing the entity contents. If not provided, the contents are printed.
            kwargs (dict): Additional parameters for filtering entity lists.
        """
        entity_view = EntityView(
            entity_id, entity_class, format, unregistered, mine_only, output, **kwargs
        )
        entity_view.validate()
        entity_view.prepare()
        if output is None:
            entity_view.display()
        else:
            entity_view.store()

    def __init__(
        self,
        entity_id: Union[int, str],
        entity_class: Type[Entity],
        format: str,
        unregistered: bool,
        mine_only: bool,
        output: str,
        **kwargs,
    ):
        self.entity_id = entity_id
        self.entity_class = entity_class
        self.format = format
        self.unregistered = unregistered
        self.mine_only = mine_only
        self.output = output
        self.filters = kwargs
        self.data = []

    def validate(self):
        valid_formats = set(["yaml", "json"])
        if self.format not in valid_formats:
            raise InvalidArgumentError("The provided format is not supported")

    def prepare(self):
        if self.entity_id is not None:
            entities = [self.entity_class.get(self.entity_id)]
        else:
            if self.mine_only:
                self.filters["owner"] = get_medperf_user_data()["id"]

            entities = self.entity_class.all(
                unregistered=self.unregistered, filters=self.filters
            )
        self.data = [entity.todict() for entity in entities]

        if self.entity_id is not None:
            # User expects a single entity if id provided
            # Don't output the view as a list of entities
            self.data = self.data[0]

    def display(self):
        if self.format == "json":
            formatter = json.dumps
        if self.format == "yaml":
            formatter = yaml.dump

        formatted_data = formatter(self.data)
        config.ui.print(formatted_data)

    def store(self):
        if self.format == "json":
            formatter = json.dump
        if self.format == "yaml":
            formatter = yaml.dump

        with open(self.output, "w") as f:
            formatter(self.data, f)
