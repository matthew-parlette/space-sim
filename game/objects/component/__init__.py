import uuid
from objects import GameObject

class Component(GameObject):
    yaml_tag = "!Component"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        key = 'component',
        count = 0,
    ):
        self.name = name
        self.id = id
        self.key = key
        self.count = count

        # Parent init should be called at end of __init__
        super(Component,self).__init__()

    def to_dict(self):
        """Override to_dict."""
        result = super(Component,self).to_dict()
        # result['coordinates'] = self.coordinates.to_dict()
        return result
