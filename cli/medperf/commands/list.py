from tabulate import tabulate

from medperf import config


class EntityList:
    @staticmethod
    def run(entity_class, local: bool = False, mine: bool = False, fields=[]):
        """Lists all local datasets

        Args:
            local (bool, optional): Display all local results. Defaults to False.
            mine (bool, optional): Display all current-user results. Defaults to False.
        """
        entity_list = EntityList(entity_class, local, mine, fields)
        entity_list.get_all()
        entity_list.filter_fields()
        entity_list.display()

    def __init__(self, entity_class, local, mine, fields):
        self.entity_class = entity_class
        self.local = local
        self.mine = mine
        self.fields = fields

    def get_all(self):
        entities = self.entity_class.all(local_only=self.local, mine_only=self.mine)
        self.dicts = [entity.todict() for entity in entities]

    def filter_fields(self):
        if "id" in self.fields:
            self.fields.remove("id")
        self.fields = ["id"] + self.fields

        self.dicts = [{dict_[field] for field in self.fields} for dict_ in self.dicts]

    def display(self):

        self.dicts = [
            {**dict_, "submitted": dict_["id"] is not None,} for dict_ in self.dicts
        ]
        data = [dict_.values() for dict_ in self.dicts]
        headers = [self.__field_as_title(field) for field in self.fields]
        tab = tabulate(data, headers=headers)
        config.ui.print(tab)

    def __field_as_title(self, field):
        return field.title().replace("_", " ").replace("Id", "ID")
