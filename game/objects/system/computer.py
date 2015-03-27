import uuid
from . import System

class Computer(System):
    yaml_tag = "!Computer"

    def __init__(
        self,
        name = "Computer",
        key = 'computer',
        id = str(uuid.uuid4()),
        version = '0.0',
    ):
        # Nothing to do here

        # Parent init should be called at end of __init__
        super(Computer,self).__init__(
            name = name,
            id = id,
            key = key,
            version = version,
        )
