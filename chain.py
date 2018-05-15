from block import Block
from transaction import TXout
import utils

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
      block = blockchain.find_block_by_hash(block.prev_hash)
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
          raise Exception("double pay")
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
        return False
      if not cur_block.isValid():
        #checks the hash
        utils.danger("cur_block {} false".format(index))
        return False
      utils.debug("warning",
        "verify prev block hash is this block prev_hash")
      if prev_block.hash != cur_block.prev_hash:
        return False
    return True

  def save(self):
    for b in self.blocks:
      b.save()
    return True

  def find_block_by_index(self, index):
    if len(self) >= index + 1:
      return self.blocks[index]
    else:
      return False

  def find_block_by_hash(self, hash):
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
      block = self.find_block_by_hash(block.prev_hash)
      if not block:
        break
    return transaction

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

  def lastblock(self):
    return self.blocks[-1]
  def maxindex(self):
    return self.blocks[-1].index
  def add_block(self, new_block):
    if new_block.index > len(self):
      pass
    self.blocks.append(new_block)
    return True
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