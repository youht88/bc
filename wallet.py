
from config import *
import utils,os,hashlib,base64
import logger

import globalVar as _global

class Wallet(object):
  def __init__(self,name=None):
    Wallet.logger = logger.logger
    Wallet.database = _global.get("database")
    if name:
      self.chooseByName(name)
  def chooseByName(self,name):
    accounts=Wallet.database["wallet"].find({"name":name})
    found=False
    for i,account in enumerate(accounts):
      if i>0:  
        raise Exception("multi account named {}".format(name))
      found = True
      self.name = name
      self.key=(account.get("prvkey"),account.get("pubkey"))
      self.pubkey64D=base64.b64encode(self.key[1]).decode()
      self.address=account.get("address")
    if not found:
      raise Exception("no such account,use function create('{}') first.".format(name))

  def chooseByAddress(self,address):
    accounts=Wallet.database["wallet"].find({"address":address})
    found=False
    for i,account in enumerate(accounts):
      if i>0:  
        raise Exception("multi account addressed {}".format(address))
      found = True
      self.name = account.get("name")
      self.key=(account.get("prvkey"),account.get("pubkey"))
      self.pubkey64D=base64.b64encode(self.key[1]).decode()
      self.address=address
    if not found:
      raise Exception("no such account,use create() first.")

  def deleteByName(name):
    Wallet.database["wallet"].remove({"name":name})
    
  def deleteByAddress(cls,address):
    Wallet.database["wallet"].remove({"address":address})
  
  def create(self,name):
    key=(prvkey,pubkey)=utils.genRSAKey("","")
    address=utils.sha256(pubkey)
    Wallet.database["wallet"].insert(
         {"name":name,"address":address,"pubkey":pubkey,"prvkey":prvkey})
    self.name = name
    self.address = address
    self.key = key
    self.pubkey64D = base64.b64encode(self.key[1]).decode()

  @property
  def isPrivate(self):
    return self.prvkey!=None 

  @staticmethod
  def address(pubkey):
    return utils.sha256(pubkey)
  
   

        
        