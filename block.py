#coding:utf-8
import hashlib
import os
import json

import utils
from config import *

from transaction import Transaction

import logger
import merkle

import globalVar as _global

class Block(object):
  def __init__(self, dictionary):
    Block.logger = logger.logger
    Block.database = _global.get("database")
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
    #merkleRoot=utils.sha256("".join(txHash))
    merkleTree = merkle.Tree()
    merkleRoot = merkleTree.makeTree(txHash)
    self.merkleRoot = merkleRoot.value
    return merkleRoot.value
  
  def updateHash(self):
    sha = hashlib.sha256()
    sha.update(self.headerString().encode())
    new_hash = sha.hexdigest()
    self.hash = new_hash
    return new_hash

  def save(self):
    Block.database["blockchain"].update({"index":self.index},{"$set":utils.obj2dict(self,sort_keys=True)},upsert=True)
  def saveToPool(self):
    index = self.index
    nonce = self.nonce
    Block.logger.warn("save block {}-{} to pool".format(index,nonce))
    Block.database["blockpool"].update({"hash":self.hash},{"$set":utils.obj2dict(self,sort_keys=True)},upsert=True)
  def removeFromPool(self):
    Block.database["blockpool"].remove({"hash":self.hash})
  def isValid(self):
    if self.index == 0:
      return True
    Block.logger.debug("verify block #{}-{}".format(str(self.index),self.nonce))
    Block.logger.debug("verify proof of work")
    self.updateHash()
    if not (str(self.hash[0:self.diffcult]) == '0' * self.diffcult):
      Block.logger.debug("%s is not worked"%self.hash)
      return False
    Block.logger.debug("%s is truly worked"%self.hash)
    Block.logger.debug("verify transaction data")
    for transaction in self.data:
      if not transaction.isValid():
        return False
    return True
      
    
  def __gt__(self, other):
    return self.timestamp < other.timestamp

  def __lt__(self, other):
    return self.timestamp > other.timestamp
