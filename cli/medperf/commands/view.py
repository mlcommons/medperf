import yaml
import json
from typing import Union

from medperf import config
from medperf.entities.interface import Entity
from medperf.exceptions import InvalidArgumentError


class EntityView:
    @staticmethod
    def run(
        entity_id: Union[int, str],
        entity_class: Entity,
        format: str = "yaml",
        local_only: bool = False,
        mine_only: bool = False,
    ):
        """Displays the contents of a single or multiple entities of a given type

        Args:
            entity_id (Union[int, str]): Entity identifies
            entity_class (Entity): Entity type
            local_only (bool, optional): Display all local entities. Defaults to False.
            mine_only (bool, optional): Display all current-user entities. Defaults to False.
            format (str, optional): What format to use to display the contents. Valid formats: [yaml, json]. Defaults to yaml.
        """
        entity_view = EntityView(entity_id, entity_class, format, local_only, mine_only)
        entity_view.prepare()
        entity_view.display()

    def __init__(self, entity_id, entity_class, format, local_only, mine_only):
        self.entity_id = entity_id
        self.entity_class = entity_class
        self.format = format
        self.local_only = local_only
        self.mine_only = mine_only
        self.data = []

    def prepare(self):
        if self.entity_id is not None:
            entities = [self.entity_class.get(self.entity_id)]
        else:
            entities = self.entity_class.all(
                local_only=self.local_only, mine_only=self.mine_only
            )
        self.data = [entity.todict() for entity in entities]

    def display(self):
        valid_formats = set("yaml", "json")
        if self.format not in valid_formats:
            raise InvalidArgumentError("The provided format is not supported")

        if self.format == "json":
            formatter = json
        if self.format == "yaml":
            formatter = yaml

        formatted_data = formatter.dumps(self.data)
        config.ui.print(formatted_data)

