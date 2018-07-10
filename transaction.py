
#coding:utf-8
from config import *
import utils
import base64
import json
import copy

import time
from wallet import Wallet
              
import logger
import globalVar as _global

class TXin(object):
  def __init__(self,dict):
    TXin.logger = logger.logger
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
    #暂停使用，移入canBeUnlockWith函数
    return True
    if not self.pubkey64D == script:
      TXin.logger.critical("canUnlockWith error:self.pubkey64D != script")
    #return self.pubkey64D == script
  def toDict(self):
    info={}
    info["prevHash"]=self.prevHash
    return info

class TXout(object):
  def __init__(self,dict):
    TXout.logger = logger.logger
    self.amount=dict["amount"]   if "amount"  in dict else None
    self.outAddr=dict["outAddr"] if "outAddr" in dict else ""
    self.script=dict["script"] if "script" in dict else ""
        
  def canbeUnlockWith(self,address):
    if self.outAddr == address :
      if self.script=="":
        return True
      else:
        #run the script 
        try:
          g={}
          l={"amount":self.amount}
          exec(self.script,g,l)
          result=l["fun"](l)
          if result==True:
            return True
          else:
            return False  
        except Exception as e:
          TXout.logger.critical("canbeUnlockWith",e)
          return False
    return False    
class Contract(object):
  def __init__(self,script,sandbox={}):
    this.status=0
    this.compileError=None
    this.executeError=None
    this.script=script
    this.sandbox=sandbox
  def _compile():
    try:
      logger.logger.critical(this.script)
      this.scriptCompiled=compile(this.script,'','exec')
    except Exception as e:
      this.compileError=e
      this.scriptCompiled=''
  def execute():
    if not this.compileError :
      try:
        exec(this.scriptCompiled,{},this.sandbox)
        return True
      except Exception as e:
        this.error=e
        return False
  def sandbox():
    return this.sandbox
    
class Transaction(object):
    def __init__(self,**args):
      Transaction.logger = logger.logger
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
      outs=[TXout({"amount":round(REWARD,4),"outAddr":outAddr,"script":""})]
      return Transaction(ins=ins,outs=outs)
   
    @staticmethod
    def newTransaction(inPrvkey,inPubkey,outPubkey,amount,utxo,script=""):
      if script:
        logger.logger.critical("check script")
        try:
          bin=compile(script,'','exec')
        except Exception as e:
          return {"errCode":2,"errText":repr(e)}
        try:
          l={"a":"x"}
          exec(bin,{},l)
          l["fun"](l)
        except Exception as e:
          return {"errCode":3,"errText":repr(e)}
      ins=[]
      outs=[]
      inAddr=Wallet.address(inPubkey)
      outAddr=Wallet.address(outPubkey)
      todo = utxo.findSpendableOutputs(inAddr,amount)
      #todo={"acc":3,"unspend":{"3453425125":{"index":0,"amount":"3"},        
      #                         "2543543543":{"index":0,"amount":"2"}
      #                        }
      #     }
      #print("newTransaction.todo","\n",todo)
      amount = round(amount,4)
      if todo["acc"] < amount:
        Transaction.logger.warning("%s not have enough money."%inAddr)
        return {"errCode":1,"errText":"not enough money."}
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
      outs.append(TXout({"amount":round(amount,4),"outAddr":outAddr,"script":script}))
      if todo["acc"] > amount:
        outs.append(TXout({"amount":round(todo["acc"]-amount,4),"outAddr":inAddr,"script":""}))
      TX = Transaction(ins=ins,outs=outs)
      utxoSet = copy.deepcopy(utxo.utxoSet)
      if not utxo.updateWithTX(TX,utxoSet):
        return {"errCode":1,"errText":"double spend!!,Maybe not enough money."}
      utxo.utxoSet = utxoSet
      return TX
  
    def isCoinbase(self):
      return self.ins[0].index==-1
   
    def sign(self,prvkey,prevTXs):
      if self.isCoinbase():
         return
      
    def isValid(self):
      if self.isCoinbase():
        return self.insLen==1 and self.outsLen==1 and self.outs[0].amount<=REWARD        
      Transaction.logger.debug("transaction","begin verify:",self.hash)
      outAddr=None
      #blockchain = _global.getValue("blockchain")
      for vin in self.ins:
        outPubkey = base64.b64decode(vin.pubkey64D.encode())
        #if blockchain:
        #  prevVout = blockchain.findOutput(vin.prevHash,vin.index)
        #  if prevVout:
        #    outAddr = prevVout.outAddr
        outAddr = vin.inAddr
        #Transaction.logger.error(amountIn,outAddr,vin.inAddr)
        #step1:verify it is mine 
        if not (outAddr == vin.inAddr and utils.sha256(outPubkey)== vin.inAddr):
          Transaction.logger.warn("transaction",outAddr,vin.inAddr)
          Transaction.logger.error("transaction",vin.prevHash,vin.index,"step1: inAddr can pass pubkey? false")
          return False
        Transaction.logger.debug("transaction",vin.prevHash,vin.index,"step1: inAddr can pass pubkey? ok")
        #step2:verify not to be changed!!!!
        isVerify=utils.verify(
          vin.prevHash+str(vin.index)+vin.inAddr,
          vin.signD.encode(),
          outPubkey
         )
        if isVerify==False:
          Transaction.logger.error("transaction",vin.prevHash,vin.index,"step2: can pass sign verify? false")
          return False
        Transaction.logger.debug("transaction",vin.prevHash,vin.index,"step2: can pass sign verify? ok")
      return True
