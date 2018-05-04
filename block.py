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
        data.append(Transaction.parseTransaction(item))
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
    return "".join([str(self.index),
        self.prev_hash,
        utils.obj2json(self.data,sort_keys=True),
        str(self.timestamp),
        str(self.diffcult),
        str(self.nonce)])
    
  def generate_header(index, prev_hash, data, timestamp, nonce):
    return "".join([str(index),
           prev_hash, 
           utils.obj2json(data,sort_keys=True),
           str(timestamp),
           str(self.diffcult),
           str(nonce)])

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
      utils.obj2jsonFile(self,block_file,sort_keys=True)

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
