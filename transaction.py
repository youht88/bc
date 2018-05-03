
#coding:utf-8
from config import *
import utils
import base64

import time

class TXin(object):
  def __init__(self,dict):
    self.prevHash='0'
    self.index=0
    self.pubkey=''
    self.sign=''
    self.inAddr=''
    if hasattr(dict,"prevHash"): self.prevHash=dict["prevHash"]
    if hasattr(dict,"index"): self.index=dict["index"]
    if hasattr(dict,"pubkey"): self.putkey=dict["pubkey"]
    if hasattr(dict,"sign"): self.sign=dict["sign"]
    if hasattr(dict,"inAddr"): self.inAddr=dict["inAddr"]
class TXout(object):
  def __init__(self,dict):
    self.amount=0
    self.outAddr=""
    if hasattr(dict,"amount"): self.value=dict["amount"]
    if hasattr(dict,"outAddr"): self.outAddr=dict["outAddr"]
class Transaction(object):
    def __init__(self,ins,outs):
      self.ins=ins
      self.outs=outs
      self.hash=utils.sha256([self.ins,self.outs])
    '''abc
    def __init__(self,dict):
        utils.dictConvert(dict,self,
            TRANSACTION_VAR_CONVERSIONS)
        self.version=1
        self.inCount=0
        self.ins=[]
        self.outCount=0
        self.outs=[]
        if not hasattr(self, 'hash'):
          #when not sync from disk or net
          outAddr = utils.sha256(dict["outPubkey"])
          inAddr  = utils.sha256(dict["inPubkey"])
          self.raw = {
            "outAddr":outAddr,
            "inAddr":inAddr,
            "amount":dict["amount"],
            "timestamp":int(time.time())
          }
          self.outPubkey = base64.b64encode(dict["outPubkey"]).decode()
          self.sign=utils.sign(self.raw,dict["outPrvkey"]).decode()
          self.hash=utils.sha256([
            self.raw,
            self.sign]
          )
    '''
    @staticmethod
    def newCoinbase(outAddr):
      ins=[{"prevHash":"","index":-1}]
      outs=[{"value":1,"outAddr":outAddr}]
      return Transaction(ins,outs)
    @staticmethod
    def newUTXO(inAddr,outAddr,amount,blockchain):
      ins=[]
      outs=[]
      todo = (acc,validOutputs)=blockchain.findSpendableOutputs(inAddr,amount)
      if todo[0] < amount:
        utils.danger("%s not have enough money."%inAddr)
      for outputs in todo[1]:
        prevHash = outputs.hash
        for output in outputs:
          input = TXin({"prevHash":prevHash,"index":0,"inAddr":inAddr})
          ins.append(input)
      outs.append(TXout({"amount":amount,"outAddr":outAddr}))
      if acc < amount:
        outs.append(TXout({"amount":acc-amount,"outAddr":inAddr}))
      return Transaction(ins,outs)

    def isValid(self):
        #self.raw["amount"]=self.raw["amount"]+0.0001
        outPubkey = base64.b64decode(self.outPubkey.encode())
        is_verify=False
        #step1:verify it is mine 
        if not utils.sha256(outPubkey)==self.raw["outAddr"]:
          return is_verify
        #step2:verify not to be changed!!!!
        is_verify=utils.verify(
          self.raw,
          self.sign.encode(),
          outPubkey
         )
        return is_verify
    def to_dict(self):
      info = {}
      info['raw']  = self.raw
      info['sign'] = self.sign
      info['hash'] = self.hash
      info['outPubkey'] = self.outPubkey
      return info
    def toDict(self):
      info={}
      info['hash']=self.hash
      info['ins']=self.ins
      info['outs']=self.outs
      return info
    def to_simple_dict(self):
      info = {}
      info["raw"]  = self.raw
      return info
