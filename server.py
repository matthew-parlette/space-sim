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
  def __init__(self,log = None,load_from_json = None):
    self.log = log if log else logging
    self.log.debug("GameEntity:__init__:JSON received as %s"
      % str(load_from_json))
    if load_from_json:
      self.log.debug("GameEntity:__init__:Loading object from JSON")
      self.load_from_json(load_from_json)

  def __repr__(self):
    return getattr(self,"name")

  def load_from_json(self,json_string):
    """Return the object represented by a json string."""
    self.log.debug("GameEntity:load_from_json:Received json_string as %s" % json_string)
    json_obj = json.loads(json_string)
    for key,default in self.__class__.properties.iteritems():
      self.log.debug("GameEntity:load_from_json:Processing property %s" % str(key))
      if key in json_obj:
        setattr(self,key,json_obj[key])
      else:
        self.log.warning("GameEntity:load_from_json:Key %s does not exist for object, defaulting to %s"
          % (str(key),str(default)))
        setattr(self,key,default)
    self.log.debug("GameEntity:load_from_json:Loaded object as %s" % str(self))
    return self

  def save_as_json(self):
    """Return a json string representing this object."""
    raise NotImplementedError

class Player(GameEntity):
  Player_properties = {'sector':'1'}
  properties = dict(GameEntity.properties.items() + Player_properties.items())

  def __repr__(self):
    return "%s (%s)" % (getattr(self,"name"),getattr(self,"sector","undefined"))

class Server(object):
  def __init__(self,log = None,num_sectors = 10):
    self.log = log if log else logging
    log.info("Server:__init__:Initializing")

    # Verify data directory structure
    log.info("Server:__init__:Verifying game data")

    # Verify top level directories
    dirs = ['universe','universe/sectors','universe/players']
    map(self.verify_dir,dirs)

    # Verify sectors
    sector_dirs = ['universe/sectors/' + str(sector)
      for sector in range(1,num_sectors + 1)]
    map(self.verify_dir,sector_dirs)

    # Verify players
    player_dirs = ['universe/players/' + str(player)
      for player in os.listdir('universe/players')
      if os.path.isdir(os.path.join('universe/players/',player))]
    map(self.verify_dir,player_dirs)

    log.info("Server:__init__:Game data verified")

  def verify_dir(self,dir,create_if_absent = True):
    """Verify that the directory exists and has a statefile.

    If it does not exist or the statefile is missing, it is created."""

    log.debug("Server:verify_dir:Verifying '%s' path" % str(dir))
    if os.path.isdir(str(dir)):
      log.debug("Server:verify_dir:Path '%s' exists" % str(dir))
    else:
      if create_if_absent:
        log.warning("Server:verify_dir:Path '%s' does not exist, it will be created" % str(dir))
        try:
          os.makedirs(str(dir))
        except:
          log.critical("Server:verify_dir:Path '%s' could not be created" % str(dir))
          sys.exit(1)
      else:
        log.warning("Server:verify_dir:Path '%s' does not exist, but create_if_absent is %s"
          % (str(dir),str(create_if_absent)))
        return False
    statefile_name = "%s/state.json" % str(dir)
    if os.path.exists(statefile_name):
      log.debug("Server:verify_dir:File '%s' exists" % str(statefile_name))
    else:
      if create_if_absent:
        log.warning("Server:verify_dir:File '%s' does not exist, it will be created" % str(statefile_name))
        with open(statefile_name, 'a'):
          os.utime(statefile_name, None)
      else:
        log.warning("Server:verify_dir:Path '%s' does not exist, but create_if_absent is %s"
          % (str(dir),str(create_if_absent)))
        return False
    return True

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

    if self.verify_dir(os.path.join('universe/players/',username),
      create_if_absent = False):
      self.log.debug("Server:load_user:User directory exists with statefile")
      # Load the user and return the object

    else:
      self.log.warning("Server:load_user:User directory does not exist, creating user %s"
        % username)
      player = Player(log = self.log, load_from_json = "{\"name\":\"%s\"}" % username)
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
