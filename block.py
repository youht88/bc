#coding:utf-8
import hashlib
import os
import json

import utils
from config import *

from transaction import Transaction

class Block(object):
  def __init__(self, dictionary):
    utils.dictConvert(dictionary,self,
        BLOCK_VAR_CONVERSIONS)
    data=[]
    if hasattr(self,'data'):
      for item in self.data:
        data.append(Transaction(item))
    self.data = data
    if not hasattr(self, 'diffcult'):
      self.diffcult = 0
    if not hasattr(self, 'nonce'):
      #we're throwin this in for generation
      self.nonce = 0
    if not hasattr(self, 'hash'): #in creating the first block, needs to be removed in future
      self.hash = self.update_self_hash()
    #print("index,diffcult,hash",self.index,self.diffcult,self.hash)
    
  def header_string(self):
    return str(self.index) + self.prev_hash + json.dumps(self.data_dict(),sort_keys=True) + str(self.timestamp) + str(self.diffcult) + str(self.nonce)
    
  def generate_header(index, prev_hash, data, timestamp, nonce):
    return str(index) + prev_hash + str(self.data_dict()) + str(timestamp) + str(self.diffcult) + str(nonce)

  def update_self_hash(self):
    sha = hashlib.sha256()
    sha.update(self.header_string().encode())
    new_hash = sha.hexdigest()
    self.hash = new_hash
    return new_hash

  def self_save(self):
    index_string = str(self.index).zfill(6) 
    filename = '%s%s.json' % (CHAINDATA_DIR, index_string)
    with open(filename, 'w') as block_file:
      json.dump(self.to_dict(),block_file,sort_keys=True)

  def to_dict(self):
    info = {}
    info['index'] = str(self.index)
    info['timestamp'] = str(self.timestamp)
    info['prev_hash'] = str(self.prev_hash)
    info['data'] = self.data_dict()
    info['hash'] = str(self.hash)
    info['diffcult'] = str(self.diffcult)
    info['nonce'] = str(self.nonce)
    return info

  def to_simple_dict(self):
    info = {}
    info['index'] = str(self.index)
    info['data'] = self.data_simple_dict()
    info['hash'] = str(self.hash)
    info['diffcult'] = str(self.diffcult)
    info['nonce'] = str(self.nonce)
    return info

  def data_dict(self):
    data = []
    for item in self.data:
      if isinstance(item,Transaction):
        data.append(item.to_dict())
      else:
        data.append(item)
    return data

  def data_simple_dict(self):
    data = []
    for item in self.data:
      if isinstance(item,Transaction):
        data.append(item.to_simple_dict())
      else:
        data.append(item)
    return data

  def is_valid(self):
    if self.index == 0:
      return True
    utils.debug("danger","verify block #"+str(self.index))
    utils.debug("success","verify proof of work")
    utils.debug("warning","old:",self.hash)
    self.update_self_hash()
    utils.debug("info","new:",self.hash)
    if not (str(self.hash[0:self.diffcult]) == '0' * self.diffcult):
      return False
    utils.debug("info","%s is truly worked"%self.hash)
    utils.debug("danger","verify transaction data")
    for transaction in self.data:
      utils.debug("info",self.data)
      transaction.isValid()
    return True
      
    
  def __repr__(self):
    return "Block<index: %s>, <hash: %s>" % (self.index, self.hash)

  def __eq__(self, other):
    return (self.index == other.index and
       self.timestamp == other.timestamp and
       self.prev_hash == other.prev_hash and
       self.hash == other.hash and
       self.data == other.data and
       self.nonce == other.nonce)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __gt__(self, other):
    return self.timestamp < other.timestamp

  def __lt__(self, other):
    return self.timestamp > other.timestamp
