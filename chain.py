from block import Block
from transaction import TXout
import utils
import json
import os

from config import *

class UTXO(object):
  def __init__(self):
    self.utxoSet=[]
  def reset(self,blockchain):
    #print(address,"\n")
    #print(utils.obj2json(self,indent=2))
    utxoSet={}
    spendInputs=[]
    block = blockchain.lastblock()
    utils.warning("blockhigh:%i"%block.index)
    while True:
      data = block.data
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
                      "outAddr":txout.outAddr})
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
    for TX in block.data:
      self.updateWithTX(TX)
    
  def updateWithTX(self,TX):   
    utxoSet=self.utxoSet
    #ins
    if TX.isCoinbase() == False:
      for idx,txin in enumerate(TX.ins):
        try:
          outs=utxoSet[txin.prevHash]
        except:
          raise Exception("double spend")
        for i,out in enumerate(outs) :
          if out["index"] == txin.index:
            del outs[i]
        if outs==[]:
          try:
            del utxoSet[txin.prevHash]
          except:
            raise Exception("double pay")
        else:
          utxoSet[txin.prevHash]=outs
    #outs
    unspendOutputs=[]
    for idx,txout in enumerate(TX.outs):
      unspendOutputs.append({
                    "index":idx,
                    "txout":TXout({"amount":txout.amount,
                                   "outAddr":txout.outAddr})
                                 })
    if not unspendOutputs==[]:
      utxoSet[TX.hash]=unspendOutputs
    self.utxoSet = utxoSet
    return utxoSet
  def updateAfterRemove(self,prevTXs,block):
    for TX in block.data:
      self.updateWithTXAfterRemove(prevTXs,TX)
  def updateWithTXAfterRemove(self,prevTXs,TX):
    utxoSet=self.utxoSet
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
                "outAddr": prevTX.outs[txin.index].outAddr})
                        })
        utxoSet[txin.prevHash] = outs
    self.utxoSet = utxoSet
    return utxoSet
  def save(self):
    filename = '%s%s.json' % (UTXO_DIR,'utxo')
    try:
      with open(filename,'w') as file:
        utils.obj2jsonFile(self.utxoSet,file)
    except Exception as e:
      utils.danger("error write utxo file.",e)
  def load(self):
    filename = '%s%s.json' % (UTXO_DIR,'utxo')
    try:
      with open(filename,'r') as file:
        self.utxoSet = json.load(file)
    except:
      utils.danger("error read utxo file.")
  def findUTXO(self,address):
    utxoSet = self.utxoSet
    findUtxoSet={}
    for hash in utxoSet:
      outs = utxoSet[hash]
      unspendOutputs=[]
      for out in outs:
        if out["txout"].canbeUnlockWith(address):
          unspendOutputs.append({"index":out["index"],"txout":out["txout"]})
      if not unspendOutputs==[]:
        findUtxoSet[hash]=unspendOutputs
    return findUtxoSet
  def getBalance(self,address):
    total=0
    utxoSet=self.findUTXO(address)
    for hash in utxoSet:
      outs = utxoSet[hash]
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
    for hash in utxoSet:
      outs = utxoSet[hash]
      for out in outs:
        acc = acc + out["txout"].amount
        unspend[hash]={"index":out["index"],"amount":out["txout"].amount}
        if acc >=amount:
          break
      if acc >= amount :
        break
    return {"acc":acc,"unspend":unspend}
      
class Chain(object):
  def __init__(self, blocks):
    self.blocks = blocks
 
  def isValid(self):
    for index, cur_block in enumerate(self.blocks[1:]):
      prev_block = self.blocks[index]
      if prev_block.index+1 != cur_block.index:
        utils.danger("index error",prev_block.index,cur_block.index)
        return False
      if not cur_block.isValid():
        #checks the hash
        utils.danger("cur_block {} false".format(index))
        return False
      if prev_block.hash != cur_block.prev_hash:
        utils.danger("block ",cur_block.index," hash error",prev_block.hash,cur_block.prev_hash)
        return False
    return True

  def save(self):
    for b in self.blocks:
      b.save()
    return True

  def findBlockByIndex(self, index):
    if len(self) >= index + 1:
      return self.blocks[index]
    else:
      return False

  def findBlockByHash(self, hash):
    for b in self.blocks:
      if b.hash == hash:
        return b
    return False
  
  def findTransaction(self,hash):
    block = self.lastblock()
    transaction=None
    while True:
      data=block.data
      for TX in data:
        if TX.hash == hash: 
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
          transactions[TX.hash]=transaction
    return transactions
  def lastblock(self):
    return self.blocks[-1]
  def maxindex(self):
    return self.blocks[-1].index
  def addBlock(self, new_block):
    if new_block.index!=0:
      if new_block.index > len(self) :
        utils.warning("new block",new_block.index,"has error index.")
        return False  
      if new_block.prev_hash != self.blocks[new_block.index - 1].hash:
        utils.warning("new block",new_block.index,"has error prev_hash.")
        return False
    #blockDict = utils.obj2dict(new_block)
    #self.blocks.append(Block(blockDict))
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
    index_string = str(index).zfill(6) 
    filename = '%s%s.json' % (CHAINDATA_DIR, index_string)
    with open(filename, 'r') as block_file:
      block = Block(json.load(block_file))
    try:
      os.remove(filename)
    except:
      pass
    self.removeBlock(block)
    block.saveToPool()

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

