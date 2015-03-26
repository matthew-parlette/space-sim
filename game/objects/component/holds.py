import uuid
from . import Component

class CargoHolds(Component):
    yaml_tag = "!CargoHolds"

    def __init__(
        self,
        name = "Cargo Holds",
        key = 'holds',
        id = str(uuid.uuid4()),
        count = 0,
    ):
        # Nothing to do here

        # Parent init should be called at end of __init__
        super(CargoHolds,self).__init__(
            name = name,
            id = id,
            key = key,
            count = count,
        )
