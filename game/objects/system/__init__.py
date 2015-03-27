import uuid
from objects import GameObject

class System(GameObject):
    yaml_tag = "!System"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        key = 'system',
        version = '0.0',
    ):
        self.name = name
        self.id = id
        self.key = key
        self.version = version

        # Parent init should be called at end of __init__
        super(System,self).__init__()

    def to_dict(self):
        """Override to_dict."""
        result = super(System,self).to_dict()
        return result
