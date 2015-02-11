import uuid
from base import GameObject
from coordinates import Coordinates

class Sector(GameObject):
    yaml_tag = "!Sector"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
    ):
        self.name = str(name)
        self.id = id

        # Parent init should be called at end of __init__
        super(Sector,self).__init__()
