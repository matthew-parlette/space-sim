import uuid
from base import GameObject

class Sector(GameObject):
    yaml_tag = "!Sector"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        warps = []
    ):
        self.name = name
        self.id = id
        self.warps = warps

        # Parent init should be called at end of __init__
        super(Sector,self).__init__()

    def __str__(self):
        return "%s (name=%s, id=%s)" % (
            self.__class__.__name__,
            self.name,
            self.id,
        )
