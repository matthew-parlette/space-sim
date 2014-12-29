import logging
import os
import sys
import json
import yaml
import uuid
import datetime

class GameObject(object):
    def __init__(self):
        # Call byteify to make sure all unicode variables are saved as strings
        # This makes it easier to save in yaml
        self.__dict__ = self.byteify(self.__dict__)

    def byteify(self, data):
        """Make sure everything in data is a string, not unicode (for nicer yaml)."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.iteritems():
                if isinstance(key, unicode):
                    key = key.encode('utf-8')
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                if isinstance(value, dict) or isinstance(value, list):
                    value = self.byteify(value)
                result[key] = value
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, unicode):
                    item = item.encode('utf-8')
                if isinstance(item, dict) or isinstance(item, list):
                    item = self.byteify(value)
        else:
            result = None

        return result

class User(GameObject):
    def __init__(self,
                 name = None,
                 password = None,
                 token = None,
                 token_expires = None):
        self.name = name
        self.password = password
        self.token = token
        self.token_expires = token_expires

        # Parent init should be called at end of __init__
        super(User,self).__init__()

    def __repr__(self):
        return "%s(name=%s, password=%s, token=%s)" % (
            self.__class__.__name__, self.name, self.password, self.token)

class Game(object):
    # Users is shared between all instances of Game
    _users = {}

    def __init__(self, data_dir = 'data', log = None):
        self.log = log
        self.file = file

        self.data_dir = data_dir
        self.log.info("Verifying data directory exists (%s)..." % str(self.data_dir))
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        self.load_shared_object('users')

        self.logged_in_user = None

    def save(self):
        self.log.info("Saving shared objects to disk")
        objects = ['users']
        for obj in objects:
            if getattr(Game, '_' + obj, None):
                self.log.info("Saving shared object '%s'..." % str(obj))
                self.log.info("Shared object '%s' is %s" % (str(obj),str(getattr(Game, '_' + obj))))
                with open(os.path.join(self.data_dir,obj + '.yaml'), 'w') as outfile:
                    outfile.write(yaml.dump(getattr(Game, '_' + obj),
                                            default_flow_style = False))
            else:
                self.log.info("'%s' shared object is empty, skipping..." % str(obj))

    def load_shared_object(self, name):
        friendly_name = name
        object_name = '_' + name
        filename = os.path.join(self.data_dir,friendly_name + '.yaml')
        self.log.info("Loading shared object '%s'" % str(friendly_name))
        # Do we need to initialize the shared object?
        if getattr(Game, object_name, None):
            self.log.info("Shared object '%s' is available" % str(friendly_name))
        else:
            self.log.info("Shared object '%s' is empty, initializing..." % str(friendly_name))
            # Shared object is empty, can we load it from a file?
            if os.path.isfile(filename):
                self.log.info("Loading shared object '%s' from %s..." % (str(friendly_name),
                                                                         str(filename)))
                setattr(Game, object_name, yaml.load(open(filename)))
            else:
                self.log.info("File not found, creating a new shared object '%s'..." %
                    str(friendly_name))

        self.log.info("load_shared_object() done, shared object '%s' is %s" %
            (str(friendly_name),str(getattr(Game, object_name))))

    def state(self):
        """Return the state and commands dictionary for the currently
        logged in user.
        """

        if self.logged_in_user:
            # User is logged in
            pass
        else:
            # No user is logged in
            empty_user = User()
            state = {'user': empty_user.__dict__}
            commands = {
                # Login takes user/pass
                'login': {'name': None, 'password': None},
                # Register takes user/pass
                'register': {'name': None, 'password': None},
            }
        self.log.info("Returning state of %s..." % str(state))

        return state, commands

    def register(self, name, password):
        if name and password:
            if name in Game._users.keys():
                self.log.error("Username '%s' already found in user database" % str(name))
                return False
            else:
                self.log.info("Adding new user '%s'..." % str(name))
                Game._users[str(name)] = User(name = name, password = password)
                return True
        self.log.error("Name or password is missing")
        return False

    def login(self, name, password):
        if name and password:
            if name in Game._users.keys():
                self.log.info("Username '%s' found in user database" % str(name))
                self.log.info("Password loaded for '%s' as '%s'" % (
                    Game._users[str(name)],
                    Game._users[str(name)].password))
                if password == Game._users[str(name)].password:
                    if Game._users[str(name)].token:
                        # Token exists
                        expires = Game._users[str(name)].token_expires
                        if datetime.datetime.strptime(expires) <= datetime.datetime.now():
                            # Token has expired, regenerate it
                            Game._users[str(name)].token = uuid.uuid4()
                            Game._users[str(name)].token_expires = datetime.timedelta(days = 1)
                            self.log.info("Login successful, token regenerated. User state is %s" % Game._users[str(name)])
                            return True
                        else:
                            # Token is still valid, user can use it
                            self.log.info("Login successful, token reused. User state is %s" % Game._users[str(name)])
                            return True
                    else:
                        # Generate token
                        Game._users[str(name)].token = uuid.uuid4()
                        Game._users[str(name)].token_expires = datetime.timedelta(days = 1)
                        self.log.info("Login successful, token generated. User state is %s" % Game._users[str(name)])
                        return True
                else:
                    self.log.error("Login failed, incorrect password for '%s'" % str(name))
                    return False
            else:
                self.log.error("Login failed, username '%s' not found in user database" % str(name))
                return False
        self.log.error("Login failed, Name or password is missing")
        return False
