
from config import *
import utils,os,hashlib,base64
import logger

class Wallete(object):
  def __init__(self,name):
    Wallete.logger = logger.logger
    try:
      os.mkdir("%s%s"%(PRIVATE_DIR,name))
    except:
      pass
    if not os.path.exists("%s%s/pubkey.pem"%(PRIVATE_DIR,name)):
      self.key=(prvkey,pubkey)=utils.genRSAKey(
             "%s%s/prvkey.pem"%(PRIVATE_DIR,name),
             "%s%s/pubkey.pem"%(PRIVATE_DIR,name))
      self.pubkey64D=base64.b64encode(pubkey).decode()
      self.address=utils.sha256(pubkey)
      with open("%s%s/%s"%(PRIVATE_DIR,name,self.address),"w") as f:
        pass
    else:
      try:
        with open("%s%s/prvkey.pem"%(PRIVATE_DIR,name),"rb") as f:
          prvkey = f.read()
      except:
        prvkey=None
      with open("%s%s/pubkey.pem"%(PRIVATE_DIR,name),"rb") as f:
        pubkey = f.read()
      if prvkey:
        self.key=(prvkey,pubkey)=(prvkey,pubkey)
      else:
        self.key=(None,pubkey)
          
      self.pubkey64D=base64.b64encode(self.key[1]).decode()
      self.address=Wallete.address(pubkey)
      if not os.path.exists("%s%s/%s"%(PRIVATE_DIR,name,self.address)):
        Wallete.logger.warn("warning : wallete address is changed excepted!")
  @staticmethod
  def address(pubkey):
    return utils.sha256(pubkey)


   

        
        