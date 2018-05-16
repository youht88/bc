
#coding:utf-8
from config import *
import utils
import base64
import json

import time
from wallete import Wallete
              
class TXin(object):
  def __init__(self,dict):
    self.prevHash=dict["prevHash"] if "prevHash" in dict else "" 
    self.index   =dict["index"]    if "index"    in dict else ""
    self.inAddr  =dict["inAddr"]   if "inAddr"   in dict else ""
    if "pubkey64D" in dict:
      self.pubkey64D=dict["pubkey64D"]
    else:
      pubkey=dict["pubkey"]   if "pubkey"   in dict else None      
      if pubkey==None:
        self.pubkey64D=""
      else:
        #64 mean use base64encode 
        self.pubkey64D=base64.b64encode(pubkey).decode()
    if "signD" in dict:
      self.signD=dict["signD"]
    else:
      sign=dict["sign"] if "sign" in dict else None
      if sign==None:
        self.signD=""
      else:
        #D  mean decode bin to str
        self.signD=sign.decode()
  def canUnlockWith(self,script):
    return True
    #return self.pubkey64D == script
  def toDict(self):
    info={}
    info["prevHash"]=self.prevHash
    return info

class TXout(object):
  def __init__(self,dict):
    self.amount=dict["amount"]   if "amount"  in dict else None
    self.outAddr=dict["outAddr"] if "outAddr" in dict else ""
  
  def canbeUnlockWith(self,script):
    return self.outAddr == script
    
class Transaction(object):
    def __init__(self,**args):
      self.ins=args["ins"]
      self.insLen=len(self.ins)
      self.outs=args["outs"]
      self.outsLen=len(self.outs)
      if "timestamp" in args:
        self.timestamp = args["timestamp"]
      else:
        self.timestamp = int(time.time())
      if "hash" in args:
        self.hash=args["hash"]
      else:
        self.hash=utils.sha256([utils.obj2json(self.ins),
                                utils.obj2json(self.outs),
                                self.timestamp])
      
    @staticmethod
    def parseTransaction(data):
      ins=[]
      outs=[]
      for txin in data["ins"]:
        ins.append(TXin(txin))
      for txout in data["outs"]:
        outs.append(TXout(txout))
      hash=data["hash"]
      timestamp=data["timestamp"]
      return Transaction(hash=hash,timestamp=timestamp,ins=ins,outs=outs)
   
    @staticmethod
    def newCoinbase(outAddr):
      ins=[TXin({"prevHash":"","index":-1,"inAddr":"","pubkey":None,"sign":None})]
      outs=[TXout({"amount":REWARD,"outAddr":outAddr})]
      return Transaction(ins=ins,outs=outs)
   
    @staticmethod
    def newTransaction(inPrvkey,inPubkey,outPubkey,amount,utxo):
      ins=[]
      outs=[]
      inAddr=Wallete.address(inPubkey)
      outAddr=Wallete.address(outPubkey)
      todo = utxo.findSpendableOutputs(inAddr,amount)
      #todo={"acc":3,"unspend":{"3453425125":{"index":0,"amount":"3"},        
      #                         "2543543543":{"index":0,"amount":"2"}
      #                        }
      #     }
      #print("newTransaction.todo","\n",todo)
      if todo["acc"] < amount:
        utils.danger("%s not have enough money."%inAddr)
        return None
      for hash in todo["unspend"]:
        output = todo["unspend"][hash]
        prevHash = hash
        index = output["index"]
        toSign=prevHash+str(index)+inAddr
        sign=utils.sign(message=toSign,prvkey=inPrvkey)
        ins.append(TXin({"prevHash":prevHash,
                         "index":index,
                         "inAddr":inAddr,
                         "pubkey":inPubkey,
                         "sign":sign}))
      outs.append(TXout({"amount":amount,"outAddr":outAddr}))
      if todo["acc"] > amount:
        outs.append(TXout({"amount":todo["acc"]-amount,"outAddr":inAddr}))
      TX = Transaction(ins=ins,outs=outs)
      utxo.updateWithTX(TX)
      return TX
  
    def isCoinbase(self):
      return self.ins[0].index==-1
   
    def sign(self,prvkey,prevTXs):
      if self.isCoinbase():
         return
      
    def isValid(self):
      if self.isCoinbase():
        return self.insLen==1 and self.outsLen==1 and self.outs[0].amount<=REWARD        
      utils.debug("warning","begin verify:",utils.obj2json(self))
      for oin in self.ins:
        outPubkey = base64.b64decode(oin.pubkey64D.encode())
        #step1:verify it is mine 
        if not utils.sha256(outPubkey)==oin.inAddr:
          return False
        utils.debug("warning",oin.prevHash,oin.index,"step1 ok")
        #step2:verify not to be changed!!!!
        isVerify=utils.verify(
          oin.prevHash+str(oin.index)+oin.inAddr,
          oin.signD.encode(),
          outPubkey
         )
        if isVerify==False:
          return False
        utils.debug("warning",oin.prevHash,oin.index,"step2 ok")
        
      return True
