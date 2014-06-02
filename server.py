#!/usr/bin/python

import argparse
import logging
import os
import sys
import socket
import json

class GameEntity(object):
  # Properties of this entity, with default values
  properties = {'name':'entity'}
  def __init__(self,state_path = None,log = None,state = None):
    self.log = log if log else logging
    self.state_path = state_path
    self.log.debug("GameEntity:__init__:Initializing object")

    # Create directories if they don't exist
    if not os.path.exists(os.path.dirname(self.state_path)):
      os.makedirs(os.path.dirname(self.state_path))

    # Create statefile if it doesn't exist
    if not os.path.exists(self.state_path):
      with open(self.state_path, 'a'):
        os.utime(self.state_path, None)

    # Load the entity state
    if not state:
      with open (self.state_path, "r") as state_file:
        state = state_file.read() #.replace('\n', '')
    self.load_state(state)

  def __repr__(self):
    return getattr(self,"name")

  def load_state(self,state):
    """Return the object represented by a json string.

    For any property to be loaded, it will be set to a default
     value if it does not exist."""
    self.log.debug("GameEntity:load_state:Received json_string as %s" % state)
    json_state = json.loads(state) if len(state) > 0 else {}
    for key,default in self.__class__.properties.iteritems():
      self.log.debug("GameEntity:load_state:Processing property %s" % str(key))
      if key in json_state:
        setattr(self,key,json_state[key])
      else:
        if key == "name": # Name is a special default
          setattr(self,key,os.path.dirname(self.state_path).split("/")[-1])
          self.log.warning("GameEntity:load_state:Name does not exist for object, setting to parent directory %s"
            % getattr(self,key))
        else:
          self.log.warning("GameEntity:load_state:Key %s does not exist for object, defaulting to %s"
            % (str(key),str(default)))
          setattr(self,key,default)
    self.log.debug("GameEntity:load_state:Loaded object as %s" % str(self))
    return self

  def save_state(self):
    """Save the current state of this object to state_path."""

    with open(self.state_path,'w+') as statefile:
      statefile.write(self.state())

  def state(self):
    """Return a json string representing this object."""
    state = {}
    for prop in self.__class__.properties.keys():
      state[prop] = getattr(self,prop)
    return json.dumps(state)

class Player(GameEntity):
  properties = {'name':'player','sector':'1'}
  # properties = dict(GameEntity.properties.items() + Player.Player_properties.items())

  def __repr__(self):
    return "%s (%s)" % (getattr(self,"name"),getattr(self,"sector","undefined"))

class Server(object):
  def __init__(self,log = None,num_sectors = 10):
    self.log = log if log else logging
    log.info("Server:__init__:Initializing")

    # Build universe reference objects
    log.info("Server:__init__:Building reference objects")

    ## Sector references
    log.debug("Server:__init__:Building sector reference")
    self.sectors = {str(sector): 'universe/sectors/' + str(sector)
      for sector in range(1,num_sectors + 1)}
    log.debug("Server:__init__:Sector reference loaded, keys are %s"
      % str(self.sectors.keys()))

    ## Player references
    log.debug("Server:__init__:Building player reference")
    if os.path.exists('universe/players'):
      self.players = {str(player): 'universe/players/' + str(player)
        for player in os.listdir('universe/players')
        if os.path.isdir(os.path.join('universe/players/',player))}
    else:
      log.debug("Server:__init__:universe/players was not found no players loaded")
      self.players = {}
    log.debug("Server:__init__:Player reference loaded, keys are %s"
      % str(self.players.keys()))

    log.info("Server:__init__:Game data verified")

  def parse_request(self,request_in):
    self.log.debug("Server:parse_request:Loading request as json")
    request = json.loads(request_in)
    self.log.info("Server:parse_request:Loaded json as %s" % str(request))
    response = {}
    if request['action'] == "login":
      self.log.info("Server:parse_request:Detected login action")
      if 'user' in request:
        player = self.load_user(request['user'])
        self.log.debug("Server:parse_request:load_user returned %s" % player)
        if player:
          self.log.info("Server:parse_request:Player %s loaded" % player)
        else:
          self.log.error("Server:parse_request:Player %s could not be found or created"
            % request['user'])
      else:
        self.log.error("Server:parse_request:User not provided in request")
      response['result'] = "success"
    else:
      response['result'] = "failure"
    self.log.info("Server:parse_request:Response is %s" % str(response))
    return json.dumps(response)

  def load_user(self,username):
    """Load a user object from a file. Returns Player object.

    If the user does not exist, it will be created."""

    self.log.debug("Server:load_user:Finding user %s" % username)
    player = None # TODO Move verify_dir to entity?

    player = Player(os.path.join('universe/players',username,'state.json'),log = self.log)

    if player:
      player.save_state()
      return player
    return None

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('-t','--test', action='store_true', help='Enable server local test mode')
  parser.add_argument('--version', action='version', version='0')
  args = parser.parse_args()

  # Setup logging options
  log_level = logging.DEBUG if args.debug else logging.INFO
  log = logging.getLogger(os.path.basename(__file__))
  log.setLevel(log_level)
  formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

  ## Console Logging
  ch = logging.StreamHandler()
  ch.setLevel(log_level)
  ch.setFormatter(formatter)
  log.addHandler(ch)

  ## File Logging
  fh = logging.FileHandler(os.path.basename(__file__) + '.log')
  fh.setLevel(log_level)
  fh.setFormatter(formatter)
  log.addHandler(fh)

  log.debug("__main__:Creating Server object")
  server = Server(log = log)

  if args.test:
    log.info("__main__:Executing server test")
    test_json = json.dumps({"action": "login","user": "matt"})
    log.debug("__main__:Test JSON request loaded as %s" % str(test_json))
    log.debug("__main__:Calling parse_request")
    result = server.parse_request(test_json)
    log.info("__main__:Test result is %s" % str(result))
  else:
    log.info("__main__:Starting TCP server")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0',10344))
    log.info("__main__:Listening for connections")
    s.listen(1)

    conn, addr = s.accept()
    log.info("__main__:Received connection from %s" % str(addr))
    while 1:
      data = conn.recv(1024)
      if not data: break
      log.info("__main__:Received data: %s" % data)
      conn.send(server.parse_request(data))
    conn.close()

  log.info("__main__:Shutting Down")
