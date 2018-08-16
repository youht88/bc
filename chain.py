#coding:utf-8

from block import Block
from transaction import TXout
import utils
import json
import os
import copy

from config import *

import logger
import globalVar as _global

class UTXO(object):
  def __init__(self,name):
    UTXO.logger = logger.logger
    UTXO.database = _global.get("database")

    # {3a75be...:[{"index":0,"txout":TXout1},{"index":1,"txout":TXout2}],
    #  m09qf3...:[{"index":0,"txout":TXout3}]}
    self.utxoSet={}
    self.name = name
    #_global.setValue("utxo.{}".format(name),self)
    #UTXO.logger.critical("utxo.{}".format(name),len(_global.getValue("utxo.{}".format(name)).utxoSet.keys()))
  #def __dict__(self):
  #  return lambda self:{"name":self.name}
  def reset(self,blockchain):
    #print(address,"\n")
    #print(utils.obj2json(self,indent=2))
    utxoSet={}
    spendInputs=[]
    block = blockchain.lastblock()
    UTXO.logger.warn("blockhigh:{}-{}".format(block.index,block.nonce))
    while True:
      data = copy.deepcopy(block.data)
      data.reverse() #import!! 倒序检查block内的交易
      for TX in data:
        unspendOutputs=[]
        for idx,txout in enumerate(TX.outs): 
          notFind=True
          for item in spendInputs:
            if TX.hash==item["hash"] and idx==item["index"]:
                notFind=False
                break
          if notFind == True:
            unspendOutputs.append({
                      "index":idx,
                      "txout":TXout({"amount":txout.amount,
                                     "outAddr":txout.outAddr,
                                     "script":txout.script})
                      })
        if not TX.isCoinbase():
          for idx,txin in enumerate(TX.ins):
            spendInputs.append({"hash":txin.prevHash,"index":txin.index})
        if not unspendOutputs==[]:
          utxoSet[TX.hash]=unspendOutputs
      block = blockchain.findBlockByHash(block.prev_hash)
      if not block:
        break
    self.utxoSet = utxoSet
    self.save()
    return utxoSet
      
  def update(self,block):
    data = copy.deepcopy(block.data)
    utxoSet = copy.deepcopy(self.utxoSet)
    for TX in data:
      if not self.updateWithTX(TX,utxoSet):
        return False
    self.utxoSet = utxoSet #maybe mem leek,check later
    return True
  def updateWithTX(self,TX,utxoSet=None):
    if not utxoSet:
      utxoSet=self.utxoSet
    #ins
    if TX.isCoinbase() == False:  
      for idx,txin in enumerate(TX.ins):
        #if #txin.prevHash=="97384dff0f5670d64b0a486b89fff64bb775279bfaa247972c672d104e9de2dd":
          #UTXO.logger.critical("error debug",utils.obj2json(utxoSet[txin.prevHash],indent=2))   
        try:
          outs=utxoSet[txin.prevHash]
        except:
          UTXO.logger.critical("1.double spend")
          return False
        findIndex = False
        for i,out in enumerate(outs) :
          if out["index"] == txin.index:
            findIndex=True
            #check out canbeUnlock?
            try:
              if txin.prevHash=="97384dff0f5670d64b0a486b89fff64bb775279bfaa247972c672d104e9de2dd":
                UTXO.logger.critical("error debug1")
              if not out["txout"].canbeUnlockWith(txin.inAddr):
                UTXO.logger.critical("0.script locked","txin:{}-{}".format(txin.prevHash,txin.index),txin.inAddr,out["txout"].outAddr)
                return False
            except Exception as e:
               UTXO.logger.critical("意外错误?",e)
               return False
            #no problem
            del outs[i]
        if findIndex==False:
          #not find prevHash-index point
          UTXO.logger.critical("2.double spend")
          return False
        if outs==[]:
          try:
            del utxoSet[txin.prevHash]
          except:
            UTXO.logger.critical("3.double spend")
            return False
        else:
          utxoSet[txin.prevHash]=outs
    #outs
    unspendOutputs=[]
    for idx,txout in enumerate(TX.outs):
      unspendOutputs.append({
                    "index":idx,
                    "txout":TXout({"amount":txout.amount,
                                   "outAddr":txout.outAddr,
                                   "script":txout.script})
                                 })
    if not unspendOutputs==[]:
      utxoSet[TX.hash]=unspendOutputs
    return True
  def updateAfterRemove(self,prevTXs,block):
    data=copy.deepcopy(block.data)
    data.reverse() #import!! 倒序检查block内的交易
    for TX in data:
      self.updateWithTXAfterRemove(prevTXs,TX)
  def updateWithTXAfterRemove(self,prevTXs,TX):
    utxoSet=copy.deepcopy(self.utxoSet)
    #outs
    outputs=utxoSet[TX.hash]
    for idx,txout in enumerate(TX.outs):
      for idx1,output in enumerate(outputs):
        if output["index"]==idx:
          del outputs[idx1]
          break
    if outputs==[]:
      del utxoSet[TX.hash]        
    else:
      utxoSet[TX.hash]=outputs
    #ins
    if TX.isCoinbase() == False:
      for idx,txin in enumerate(TX.ins):
        try:
          outs=utxoSet[txin.prevHash]
        except:
          outs=[]
        prevTX=prevTXs[txin.prevHash]
        prevOuts = prevTX.outs
        outs.append({
            "index":txin.index,
            "txout":TXout({
                "amount" : prevTX.outs[txin.index].amount,
                "outAddr": prevTX.outs[txin.index].outAddr,
                "script" : prevTX.outs[txin.index].script})
                        })
        utxoSet[txin.prevHash] = outs
    self.utxoSet = utxoSet
    return utxoSet
  def save(self):
    try:
      UTXO.database["utxo"].remove({})
      UTXO.database["utxo"].insert(utils.obj2dict(self.utxoSet))
    except Exception as e:
      UTXO.logger.error("error write utxo file. {}".format(e))
  def load(self):
    try:
      self.utxoSet = [item for item in UTXO.database["utxo"].find()]
    except:
      UTXO.logger.error("error read utxo file.")
  def findUTXO(self,address):
    utxoSet = self.utxoSet
    findUtxoSet={}
    for uhash in utxoSet:
      outs = utxoSet[uhash]
      unspendOutputs=[]
      for out in outs:
        if out["txout"].canbeUnlockWith(address):
          unspendOutputs.append({"index":out["index"],"txout":out["txout"]})
      if not unspendOutputs==[]:
        findUtxoSet[uhash]=unspendOutputs
    return findUtxoSet
  def getBalance(self,address):
    total=0
    utxoSet=self.findUTXO(address)
    for uhash in utxoSet:
      outs = utxoSet[uhash]
      for out in outs:
        total = total + out["txout"].amount
    return total
  def getSummary(self):
    total=0
    txs=0
    for txHash in self.utxoSet:
      txs +=1
      outs = self.utxoSet[txHash]
      for out in outs:
        total += out["txout"].amount
    return {"txs":txs,"total":total}
  def findSpendableOutputs(self,address,amount):
    acc=0
    unspend = {}
    utxoSet = self.findUTXO(address)
    for uhash in utxoSet:
      outs = utxoSet[uhash]
      for out in outs:
        acc = acc + out["txout"].amount
        unspend[uhash]={"index":out["index"],"amount":out["txout"].amount}
        if acc >=amount:
          break
      if acc >= amount :
        break
    return {"acc":acc,"unspend":unspend}
      
class Chain(object):
  def __init__(self, blocks):
    Chain.logger = logger.logger
    _global.set("blockchain",self)
    Chain.database = _global.get("database")
    self.blocks = blocks
    self.utxo = UTXO('main')
  def isValid(self):
    for index, cur_block in enumerate(self.blocks[1:]):
      prev_block = self.blocks[index]
      if prev_block.index+1 != cur_block.index:
        Chain.logger.error("index error",prev_block.index,cur_block.index)
        return False
      if not cur_block.isValid():
        #checks the hash
        Chain.logger.error("cur_block {}-{}  false".format(index,cur_block.nonce))
        return False
      if prev_block.hash != cur_block.prev_hash:
        Chain.logger.error("block ",cur_block.index," hash error",prev_block.hash,cur_block.prev_hash)
        return False
    return True

  def save(self):
    for b in self.blocks:
      b.save()
    return True
  
  def findOutput(self,txHash,index):
    block=self.lastblock()
    bindex=block.index
    while bindex >= 0:
      TXs = block.data
      for tx in TXs:
        if tx.hash == txHash:
          try:
            vout = tx.outs[index]
            return vout
          except:
            Chain.logger.error("!!",txHash,index,tx.hash)
            return None
      bindex = bindex -1
      block = self.findBlockByIndex(bindex)   
    return None   
  
  def findBlockByIndex(self, index):
    if index<0:
      return None
    if len(self) >= index + 1:
      return self.blocks[index]
    else:
      return False

  def findBlockByHash(self, uhash):
    for b in self.blocks:
      if b.hash == uhash:
        return b
    return False
  
  def findTransaction(self,uhash):
    block = self.lastblock()
    transaction=None
    while True:
      data=block.data
      for TX in data:
        if TX.hash == uhash: 
          transaction = TX
          break
      block = self.findBlockByHash(block.prev_hash)
      if not block:
        break
    return transaction
  def findPrevTransactions(self,block):
    transactions={}
    for TX in block.data:
      #忽略coinbase
      if TX.isCoinbase():
        continue
      for ins in TX.ins:
        transaction = self.findTransaction(ins.prevHash)
        if transaction:
          transactions[transaction.hash]=transaction
    return transactions
  def lastblock(self):
    if len(self.blocks)==0:
      return None
    return self.blocks[-1]
  def maxindex(self):
    if len(self.blocks)==0:
      return None
    return self.blocks[-1].index
  def addBlock(self, new_block):
    if new_block.index >= 1:
      if new_block.index > len(self) :
        Chain.logger.warn("new block {}-{} has error index.".format(new_block.index,new_block.nonce))
        return False  
      if new_block.prev_hash != self.blocks[new_block.index - 1].hash:
        Chain.logger.warn("new block {}-{} has error prev_hash.".format(new_block.index,new_block.nonce))
        return False
      self.blocks.append(new_block)
    elif new_block.index==0:
      self.blocks.append(new_block)
    return True
  def removeBlock(self,old_block):
    index = old_block.index
    data  = old_block.data
    del self.blocks[index]
    prevTXs=self.findPrevTransactions(old_block)
    self.utxo.updateAfterRemove(prevTXs,old_block)
  def findRangeBlocks(self,fromIndex,toIndex):
    maxindex = self.maxindex()
    if fromIndex<0 or fromIndex>maxindex:
      return False
    if toIndex<fromIndex or toIndex>maxindex:
      return False
    blocks=[]
    for i in range(fromIndex,toIndex+1):
      blocks.append(self.blocks[i])
    return blocks
  def moveBlockToPool(self,index):
    blockDict = Chain.database["blockchain"].find_one({"index":index},{"_id":0})
    block = Block(blockDict)
    try:
      Chain.database["blockchain"].remove({"index":index})
    except:
      pass
    Chain.logger.warn("remove block {}-{} from chain".format(block.index,block.nonce))
    self.removeBlock(block)
    block.saveToPool()
  def getSPV(self):
    blockSPV=[]
    for block in self.blocks:
      item = {"txCount":len(block.data),
              "diffcult": block.diffcult, 
              "hash":block.hash, 
              "index": block.index, 
              "merkleRoot":block.merkleRoot,  
              "nonce": block.nonce, 
              "prev_hash":block.prev_hash,  
              "timestamp": block.timestamp}
      blockSPV.append(item)
    return blockSPV        
  def __len__(self):
    return len(self.blocks)

  def __eq__(self, other):
    if len(self) != len(other):
      return False
    for self_block, other_block in zip(self.blocks, other.blocks):
      if self_block != other_block:
        return False
    return True

  def __ne__(self, other):
    return not self.__eq__(other)

  def __gt__(self, other):
    return len(self.blocks) > len(other.blocks)

  def __lt__(self, other):
    return len(self.blocks) < len(other.blocks)

  def __ge__(self, other):
    return self.__eq__(other) or self.__gt__(other)

  def __le__(self, other):
    return self.__eq__(other) or self.__lt__(other)

