#!/usr/bin/python

import argparse
import logging
import os
import pickle
import glob
from uuid import uuid4

log = None

class Entity(object):
  """Entity base class"""
  def __init__(self, name, id = uuid4()):
    # super(Entity, self).__init__()
    self.id = id
    self.name = name

  def __hash__(self):
    return hash(self.id)

  def __repr__(self):
    return "%s %s" % (self.__class__.__name__,self.name)

class Sector(Entity):
  """Sector object"""
  def __init__(self, name, warps = []):
    super(Sector, self).__init__(name = name,id = name)
    self.warps = warps

  def __hash__(self):
    return hash(self.name)

  def add_warp(self, sector_id):
    if sector_id not in self.warps:
      self.warps.append(str(sector_id))
    return True

class Player(Entity):
  """Player class"""
  def __init__(self, name, id = uuid4()):
    super(Player, self).__init__(name = name, id = id)

class Server(object):
  def __init__(self,path):
    self.log = log
    self.base_path = path
    self.sectors_path = os.path.join(path,"universe/sectors")
    self.entities_path = os.path.join(path,"universe/entities")
    if not os.path.exists(self.sectors_path): os.makedirs(self.sectors_path)
    if not os.path.exists(self.entities_path): os.makedirs(self.entities_path)
    self.load_sectors(self.sectors_path)
    self.load_entities(self.entities_path)
    self.log.debug("Server initialized, %i sectors loaded" % len(self.sectors))

  def sector_map(self):
    """Return a string of the universe sector layout"""
    result = ""
    for s in self.sectors.keys():
      result += "%s => %s\n" % (str(s),str(s.warps))
    return result

  def create_entity(self, entity):
    if entity.__class__.__name__ == "Sector":
      if entity not in self.sectors:
        self.log.debug("Adding %s to sectors" % entity)
        self.sectors[entity] = os.path.join(self.sectors_path,"%s.pickle" % entity.id)
        self.save_entity(entity,self.sectors[entity])
      self.log.debug("Added sector, %i sectors currently loaded" % len(self.sectors))
      return True
    else:
      if entity not in self.entities:
        self.entities[entity] = os.path.join(self.entities_path,"%s.pickle" % entity.id)
        self.save_entity(entity,self.entities[entity])
      self.log.debug("Added entity, %i entities currently loaded" % len(self.entities))
      return True
    return False

  def big_bang(self):
    self.log.info("Executing big bang")
    self.log.debug("Deleting sectors")
    files = glob.glob(os.path.join(self.sectors_path,'*'))
    for f in files:
      os.remove(f)
    self.log.debug("Deleting entities")
    files = glob.glob(os.path.join(self.entities_path,'*'))
    for f in files:
      os.remove(f)
    self.load_sectors(self.sectors_path) # Should clear the sector list
    self.load_entities(self.entities_path) # Should clear the entities list
    self.log.info("Adding sectors")
    s1 = Sector("1",warps = ['2','3','4','5'])
    s2 = Sector("2",warps = ['1','3','4','5'])
    s3 = Sector("3",warps = ['1','2','4','5'])
    s4 = Sector("4",warps = ['1','2','3','5'])
    s5 = Sector("5",warps = ['1','2','3','4'])
    # 5 sector universe
    self.create_entity(s1)
    self.create_entity(s2)
    self.create_entity(s3)
    self.create_entity(s4)
    self.create_entity(s5)

  def save_entity(self,entity,filename):
    pickle.dump( entity, open( filename, "wb" ) )
    return True

  def load_entity(self,filename):
    return pickle.load( open( filename, "rb" ) )

  def load_sectors(self,path):
    """Load all sectors in the given path"""
    self.log.debug("Loading sectors from %s" % path)
    self.sectors = {}
    for file in os.listdir(path):
      if file.endswith(".pickle"):
        self.log.debug("Loading sector from %s" % file)
        entity = self.load_entity(os.path.join(path,file))
        if entity not in self.sectors.keys():
          self.log.debug("Adding sector (%s) to sectors list" % entity)
          self.sectors[entity] = os.path.join(path,file)

  def load_entities(self,path):
    """Load all entities in the given path"""
    self.log.debug("Loading entities from %s" % path)
    self.entities = {}
    for file in os.listdir(path):
      if file.endswith(".pickle"):
        self.log.debug("Loading entity from %s" % file)
        entity = self.load_entity(os.path.join(path,file))
        if entity not in self.entities.keys():
          self.log.debug("Adding entity (%s) to entities list" % entity)
          self.entities[entity] = os.path.join(path,file)

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('--bigbang', action='store_true', help='Reset universe')
  parser.add_argument('-t','--test', action='store_true', help='Test server functionality')
  parser.add_argument('--version', action='version', version='0')
  args = parser.parse_args()

  # Setup logging options
  log_level = logging.DEBUG if args.debug else logging.INFO
  global log
  log = logging.getLogger(os.path.basename(__file__))
  log.setLevel(log_level)
  formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(funcName)s(%(lineno)i):%(message)s')

  ## Console Logging
  ch = logging.StreamHandler()
  ch.setLevel(log_level)
  ch.setFormatter(formatter)
  log.addHandler(ch)

  ## File Logging
  # fh = logging.FileHandler(os.path.basename(__file__) + '.log')
  # fh.setLevel(log_level)
  # fh.setFormatter(formatter)
  # log.addHandler(fh)

  log.info("Initializing Server")
  server = Server(path = "test" if args.test else "")

  if args.bigbang:
    log.warning("Executing big bang")
    server.big_bang()

  if args.test:
    log.info("Running server functionality tests")
    server.big_bang()
    server.create_entity(Player("test player"))

    print "Sector Map\n=========="
    print server.sector_map()

    print "Game Objects\n============"
    print "\n".join(str(s) for s in server.entities.keys())
