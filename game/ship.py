import uuid
from base import GameObject

class Ship(GameObject):
    yaml_tag = "!Ship"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        location_id = None,
    ):
        self.name = name
        self.id = id
        self.location_id = location_id

        # Parent init should be called at end of __init__
        super(Ship,self).__init__()

    def __str__(self):
        return "%s (name=%s, id=%s)" % (
            self.__class__.__name__,
            self.name,
            self.id,
        )
