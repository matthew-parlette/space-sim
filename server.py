#!/usr/bin/python

import argparse
import logging
import os
import sys

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

  log.info("Initializing")

  # Verify data directory structure
  log.info("Verifying game data")

  dirs = ['universe']

  for d in dirs:
    log.debug("Verifying '%s' path" % str(d))
    if os.path.isdir(str(d)):
      log.debug("Path '%s' exists" % str(d))
    else:
      log.warning("Path '%s' does not exist, it will be created" % str(d))
      try:
        os.makedirs(str(d))
      except:
        log.critical("Path '%s' could not be created" % str(d))
        sys.exit(1)
    statefile_name = "%s/state.json" % str(d)
    if os.path.exists(statefile_name):
      log.debug("File '%s' exists" % str(statefile_name))
    else:
      log.warning("File '%s' does not exist, it will be created" % str(statefile_name))
      with open(statefile_name, 'a'):
        os.utime(statefile_name, times)

  log.info("Game data verified")

  log.info("Shutting Down")
