import uuid
from base import GameObject
from coordinates import Coordinates

class Ship(GameObject):
    yaml_tag = "!Ship"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        coordinates = Coordinates(0,0,0),
    ):
        self.name = name
        self.id = id
        self.coordinates = coordinates

        # Parent init should be called at end of __init__
        super(Ship,self).__init__()
