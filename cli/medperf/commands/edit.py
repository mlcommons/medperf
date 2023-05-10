from medperf.entities.interface import Updatable
from medperf.exceptions import InvalidEntityError

class EntityEdit:
    @staticmethod
    def run(entity_class, id: str, fields: dict):
        """Edits and updates an entity both locally and on the server if possible

        Args:
            entity (Editable): Entity to modify
            fields (dict): Dicitonary of fields and values to modify
        """
        editor = EntityEdit(entity_class, id, fields)
        editor.prepare()
        editor.validate()
        editor.edit()

    def __init__(self, entity_class, id, fields):
        self.entity_class = entity_class
        self.id = id
        self.fields = fields

    def prepare(self):
        self.entity = self.entity_class.get(self.id)
        # Filter out empty fields
        self.fields = {k: v for k, v in self.fields.items() if v is not None}

    def validate(self):
        if not isinstance(self.entity, Updatable):
            raise InvalidEntityError("The passed entity can't be edited") 

    def edit(self):
        entity = self.entity
        entity.edit(**self.fields)

        if isinstance(entity, Updatable) and entity.is_registered:
            entity.update()

        entity.write()