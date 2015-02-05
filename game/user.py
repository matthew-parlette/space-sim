from base import GameObject

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

    def __str__(self):
        return "%s (name=%s, status=%s)" % (
            self.__class__.__name__, self.name, self.status)
