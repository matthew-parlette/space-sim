#!/usr/bin/python

import argparse
import logging
import os

class Game(object):
  """docstring for Game"""
  def __init__(self, log = None):
    super(Game, self).__init__()
    self.log = log
    log.debug("%s initialized" % self.__class__.__name__)

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('--version', action='version', version='0.0')
  args = parser.parse_args()

  # Setup logging options
  log_level = logging.DEBUG if args.debug else logging.INFO
  log = logging.getLogger(os.path.basename(__file__))
  log.setLevel(log_level)
  # TODO: change name to be class name
  formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(funcName)s(%(lineno)i):%(message)s')

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

  log.info("Initializing game...")
  game = Game(log)
