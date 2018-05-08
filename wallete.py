
from config import *
import utils,os,hashlib

class Wallete(object):
  def __init__(self,name):
    try:
      os.mkdir("%s%s"%(PRIVATE_DIR,name))
    except:
      pass
    if not os.path.exists("%s%s/pvkey.pem"%(PRIVATE_DIR,name)):
      self.key=(pvkey,pbkey)=utils.genRSAKey(
             "%s%s/pvkey.pem"%(PRIVATE_DIR,name),
             "%s%s/pbkey.pem"%(PRIVATE_DIR,name))
      self.address=utils.sha256(pbkey)
      with open("%s%s/%s"%(PRIVATE_DIR,name,self.address),"w") as f:
        pass
    else:
      with open("%s%s/pvkey.pem"%(PRIVATE_DIR,name),"rb") as f:
              pvkey = f.read()
      with open("%s%s/pbkey.pem"%(PRIVATE_DIR,name),"rb") as f:
              pbkey = f.read()
      self.key=(pvkey,pbkey)=(pvkey,pbkey)
      self.address=Wallete.address(pbkey)
      if not os.path.exists("%s%s/%s"%(PRIVATE_DIR,name,self.address)):
        print("warning : wallete address is changed excepted!")
  @staticmethod
  def address(pbkey):
    return utils.sha256(pbkey)


   

        
        