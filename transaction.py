
#coding:utf-8
from config import *
import utils
import base64
import json

import time

class UTXO(object):
  @staticmethod
  def reindex(blockchain):
    pass
  @staticmethod
  def findSpendableOutputs(object):
    pass
  @staticmethod
  def findUTXO():
    pass
class TXin(object):
  def __init__(self,dict):
    self.prevHash=dict["prevHash"] if "prevHash" in dict else "" 
    self.index   =dict["index"]    if "index"    in dict else ""
    pubkey=dict["pubkey"]   if "pubkey"   in dict else None      
    if pubkey==None:
      self.pubkey64D=""
    else:
      #64 mean use base64encode 
      self.pubkey64D=base64.b64encode(pubkey).decode()
    sign=dict["sign"] if "sign" in dict else None
    if sign==None:
      self.signD=""
    else:
      #D  mean decode bin to str
      self.signD=sign.decode()
  def toDict(self):
    info={}
    info["prevHash"]=self.prevHash
    return info
  def toJson(self):
    return json.dumps(self,sort_keys=True) 
class TXout(object):
  def __init__(self,dict):
    self.amount=dict["amount"]   if "amount"  in dict else None
    self.outAddr=dict["outAddr"] if "outAddr" in dict else ""
  def toJson(self):
    return json.dumps(self.__dict__,sort_keys=True)
class Transaction(object):
    def __init__(self,**args):
      self.ins=args["ins"]
      self.insLen=len(self.ins)
      self.outs=args["outs"]
      self.outsLen=len(self.outs)
      if "hash" in args:
        self.hash=args["hash"]
      else:
        self.hash=utils.sha256([self.ins,self.outs])
      
    @staticmethod
    def parseTransaction(data):
      ins=[]
      outs=[]
      for txin in data["ins"]:
        ins.append(TXin(txin))
      for txout in data["outs"]:
        outs.append(TXout(txout))
      hash=data["hash"]
      return Transaction(hash=hash,ins=ins,outs=outs)
    @staticmethod
    def newCoinbase(outAddr):
      ins=[TXin({"prevHash":"","index":-1,"pubkey":None,"sign":None})]
      outs=[TXout({"amount":1,"outAddr":outAddr})]
      return Transaction(ins=ins,outs=outs)
    @staticmethod
    def newTransaction(inAddr,outAddr,amount,blockchain):
      ins=[]
      outs=[]
      #todo = (acc,validOutputs)=blockchain.findSpendableOutputs(inAddr,amount)
      todo=(3,[{"hash":"abc","unspend":[{"index":0,"outAddr":"a"}]},
               {"hash":"xyz","unspend":[{"index":0,"outAddr":"a"}]}
              ])
      if todo[0] < amount:
        utils.danger("%s not have enough money."%inAddr)
        return
      for outputs in todo[1]:
        prevHash = outputs["hash"]
        for output in outputs["unspend"]:
          ins.append(
            TXin({"prevHash":prevHash,"index":output["index"],"pubkey":None,"sign":None}))
      outs.append(
        TXout({"amount":amount,"outAddr":outAddr}))
      if todo[0] > amount:
        outs.append(TXout({"amount":todo[0]-amount,"outAddr":inAddr}))
      return Transaction(ins=ins,outs=outs)
    def isCoinbase(self):
      return self.index==-1
    def sign(self,prvkey,prevTXs):
      if iscoinbase(self):
         return
      
    def isValid(self):
        return True
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
