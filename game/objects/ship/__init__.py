import uuid
from objects import GameObject
from objects.coordinates import Coordinates

class Ship(GameObject):
    yaml_tag = "!Ship"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        coordinates = Coordinates(0,0,0),
        components = [],
        systems = [],
    ):
        self.name = name
        self.id = id
        self.coordinates = coordinates
        self.components = components
        self.systems = systems

        # Parent init should be called at end of __init__
        super(Ship,self).__init__()

    def to_dict(self):
        """Override to_dict to handle coordinates."""
        result = super(Ship,self).to_dict()
        result['coordinates'] = self.coordinates.to_dict()
        result['components'] = [c.to_dict() for c in self.components]
        result['systems'] = [s.to_dict() for s in self.systems]
        return result
