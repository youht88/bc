
from config import *
import utils,os,hashlib,base64

class Wallete(object):
  def __init__(self,name):
    try:
      os.mkdir("%s%s"%(PRIVATE_DIR,name))
    except:
      pass
    if not os.path.exists("%s%s/prvkey.pem"%(PRIVATE_DIR,name)):
      self.key=(prvkey,pubkey)=utils.genRSAKey(
             "%s%s/prvkey.pem"%(PRIVATE_DIR,name),
             "%s%s/pubkey.pem"%(PRIVATE_DIR,name))
      self.address=utils.sha256(pubkey)
      with open("%s%s/%s"%(PRIVATE_DIR,name,self.address),"w") as f:
        pass
    else:
      
      with open("%s%s/prvkey.pem"%(PRIVATE_DIR,name),"rb") as f:
              prvkey = f.read()
      with open("%s%s/pubkey.pem"%(PRIVATE_DIR,name),"rb") as f:
              pubkey = f.read()
      self.key=(prvkey,pubkey)=(prvkey,pubkey)
      self.pubkey64D=base64.b64encode(self.key[1]).decode()
      self.address=Wallete.address(pubkey)
      if not os.path.exists("%s%s/%s"%(PRIVATE_DIR,name,self.address)):
        print("warning : wallete address is changed excepted!")
  @staticmethod
  def address(pubkey):
    return utils.sha256(pubkey)


   

        
        