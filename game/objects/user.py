from objects import GameObject

class User(GameObject):
    yaml_tag = "!User"

    STATUS = [
        'new',
        'alive',
        'dead',
    ]

    def __init__(
        self,
        name = None,
        password = None,
        token = None,
        status = 'new',
        location_id = None
    ):
        self.name = name
        self.password = password
        self.token = token
        self.status = status
        self.location_id = location_id

        # Parent init should be called at end of __init__
        super(User,self).__init__()
