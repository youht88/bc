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
      self.hash = self.updateHash()
    #print("index,diffcult,hash",self.index,self.diffcult,self.hash)
    
  def headerString(self):
    return "".join([str(self.index),
        self.prev_hash,
        self.getMerkleRoot(),
        str(self.timestamp),
        str(self.diffcult),
        str(self.nonce)])
  def getMerkleRoot(self):
    txHash=[]
    for item in self.data:
      txHash.append(item.hash)
    merkleRoot=utils.sha256("".join(txHash))
    return merkleRoot
  '''  
  def generate_header(index, prev_hash, data, timestamp, nonce):
    return "".join([str(index),
           prev_hash, 
           utils.obj2json(data,sort_keys=True),
           str(timestamp),
           str(self.diffcult),
           str(nonce)])
  '''
  
  def updateHash(self):
    sha = hashlib.sha256()
    sha.update(self.headerString().encode())
    new_hash = sha.hexdigest()
    self.hash = new_hash
    return new_hash

  def save(self):
    index_string = str(self.index).zfill(6) 
    filename = '%s%s.json' % (CHAINDATA_DIR, index_string)
    with open(filename, 'w') as block_file:
      utils.obj2jsonFile(self,block_file,sort_keys=True)
  def saveToPool(self):
    index = self.index
    nonce = self.nonce
    filename = BROADCASTED_BLOCK_DIR + '%s_%s.json' % (index, nonce)
    with open(filename, 'w') as block_file:
      utils.obj2jsonFile(self, block_file,sort_keys=True)

  def isValid(self):
    if self.index == 0:
      return True
    utils.debug("danger","verify block #"+str(self.index))
    utils.debug("danger","verify proof of work")
    self.updateHash()
    if not (str(self.hash[0:self.diffcult]) == '0' * self.diffcult):
      return False
    utils.debug("success","%s is truly worked"%self.hash)
    utils.debug("danger","verify transaction data")
    for transaction in self.data:
      utils.debug("info",self.data)
      if not transaction.isValid():
        return False
    return True
      
    
  def __gt__(self, other):
    return self.timestamp < other.timestamp

  def __lt__(self, other):
    return self.timestamp > other.timestamp
