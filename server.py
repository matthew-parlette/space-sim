#!/usr/bin/python

import argparse
import logging
import os
import sys
import socket
import json

class Server(object):
  def __init__(self,log = None):
    self.log = log if log else logging
    log.info("Server:__init__:Initializing")

    # Verify data directory structure
    log.info("Server:__init__:Verifying game data")

    # Top level directories
    dirs = ['universe','universe/sectors','universe/players']

    # Verify directory and statefile exists
    map(self.verify_dir,dirs)

    log.info("Server:__init__:Game data verified")

  def verify_dir(self,dir):
    """Verify that the directory exists and has a statefile.

    If it does not exist or the statefile is missing, it is created."""

    log.debug("Server:verify_dir:Verifying '%s' path" % str(dir))
    if os.path.isdir(str(dir)):
      log.debug("Server:verify_dir:Path '%s' exists" % str(dir))
    else:
      log.warning("Server:verify_dir:Path '%s' does not exist, it will be created" % str(dir))
      try:
        os.makedirs(str(dir))
      except:
        log.critical("Server:verify_dir:Path '%s' could not be created" % str(dir))
        sys.exit(1)
    statefile_name = "%s/state.json" % str(dir)
    if os.path.exists(statefile_name):
      log.debug("Server:verify_dir:File '%s' exists" % str(statefile_name))
    else:
      log.warning("Server:verify_dir:File '%s' does not exist, it will be created" % str(statefile_name))
      with open(statefile_name, 'a'):
        os.utime(statefile_name, None)

  def parse_request(self,request_in):
    self.log.debug("Server:parse_request:Loading request as json")
    request = json.loads(request_in)
    self.log.info("Server:parse_request:Loaded json as %s" % str(request))
    response = {}
    if request['action'] == "login":
      self.log.info("Server:parse_request:Detected login action")
      response['result'] = "success"
    else:
      response['result'] = "failure"
    self.log.info("Server:parse_request:Response is %s" % str(response))
    return json.dumps(response)

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
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

  # Sectors
  # dirs += ['universe/sectors/' + str(sector) for sector in range(1,11)]

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
