#coding:utf-8
import hashlib

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.Hash import SHA
import base64

import json

from config import *

import threading,queue,multiprocessing
import platform
from  enum import Enum

def genRSAKey(prvfile="private.pem",pubfile="public.pem"):
  #only a sample for test
  random_generate=Random.new().read
  rsa = RSA.generate(1024,random_generate)

  private_pem = rsa.exportKey()
  
  if not prvfile=="":
    with open(prvfile,'wb') as f:
      f.write(private_pem)

  public_pem=rsa.publickey().exportKey()
  
  if not pubfile=="":
    with open(pubfile,'wb') as f:
      f.write(public_pem)
  
  return (private_pem,public_pem)
    
def encrypt(message,pubkey=None,pubfile=None):
  cipher_text="ERROR"
  if isinstance(message,dict):
    message = json.dumps(message,sort_keys=True)
  try:
    if pubfile :
      try:
        with open(pubfile,"rb") as f:
          key = f.read()
      except:
        pass
    else:
      key = pubkey
    rsakey = RSA.importKey(key)  # 导入读取到的公钥
    cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 生成对象
    cipher_text = base64.b64encode(cipher.encrypt(message.encode(encoding="utf-8")))  # 通过生成的对象加密message明文，注意，在python3中加密的数据必须是bytes类型的数据，不能是str类型的数据
  except:
    pass
  #print("\033[1;31;47mencrypt:\033[0m",cipher_text)
  return cipher_text
  
def decrypt(cipher_text,prvkey=None,prvfile=None):
  text="ERROR"
  try:
    if prvfile:
      try:
        with open(prvfile,"rb") as f:
          key = f.read()
      except:
        pass
    else:
      key = prvkey
    rsakey = RSA.importKey(key)  # 导入读取到的私钥
    cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 生成对象
    text = cipher.decrypt(base64.b64decode(cipher_text), "ERROR")  # 将密文解密成明文，返回的是一个bytes类型数据，需要自己转换成str
  except:
    pass
  #print("\033[1;31;47mdecrypt:\033[0m",text,"\n")
  return(text)  

def sign(message,prvkey=None,prvfile=None):
  signature="ERROR"
  if isinstance(message,dict):
    message = json.dumps(message,sort_keys=True)
  try:
    if prvfile:
      try:
        with open(prvfile,"rb") as f:
          key = f.read()
      except:
        pass
    else:
      key = prvkey
      
    rsakey = RSA.importKey(key)
    signer = Signature_pkcs1_v1_5.new(rsakey)
    digest = SHA.new()
    digest.update(message.encode())
    sign = signer.sign(digest)
    signature = base64.b64encode(sign)
  except:
    pass
  #print("\033[1;31;47msign:\033[0m",signature)
  return(signature)
  
def verify(message,signature,pubkey=None,pubfile=None):
  is_verify=False
  if isinstance(message,dict):
    message = json.dumps(message,sort_keys=True)
  try:
    if pubfile:
      try:
        with open(pubfile,"rb") as f:
          key = f.read()
      except:
        pass
    else:
      key = pubkey  
    rsakey = RSA.importKey(key)
    verifier = Signature_pkcs1_v1_5.new(rsakey)
    digest = SHA.new()
    # Assumes the data is base64 encoded to begin with
    digest.update(message.encode())
    is_verify = verifier.verify(digest, base64.b64decode(signature))
  except:
    pass
  #print("\033[1;31;47mverify:\033[0m",is_verify)
  return(is_verify)
  
def sha256(data):
  source=[]
  if isinstance(data,list):
    source=data
  else:
    source.append(data)
  sha256=hashlib.sha256()
  for item in source:
    temp=item
    if isinstance(item,dict):
       try:
         temp = json.dumps(temp,sort_keys=True)
       except Exception as e:
         print(str(e))
         return None
    temp = str(temp).encode()
    sha256.update(temp)      
  return sha256.hexdigest()
  
def danger(*data):
  if len(data)==1:
    print("\033[1;31m"+str(data[0])+"\033[0m")
  else:
    print("\033[1;31m"+" ".join(str(i) for i in data)+"\033[0m")
def success(*data):
  if len(data)==1:
    print("\033[1;32m"+str(data[0])+"\033[0m")
  else:
    print("\033[1;32m"+" ".join(str(i) for i in data)+"\033[0m")
def warning(*data):
  if len(data)==1:
    print("\033[1;33m"+str(data[0])+"\033[0m")
  else:
    print("\033[1;33m"+" ".join(str(i) for i in data)+"\033[0m")
def info(*data):
  if len(data)==1:
    print("\033[1;34m"+str(data[0])+"\033[0m")
  else:
    print("\033[1;34m"+" ".join(str(i) for i in data)+"\033[0m")

def debug(level,*data):
  if DEBUG_MODE:
    if level=="danger":
      danger(data)
    elif level=="info":
      info(data)
    elif level=="success":
      success(data)
    elif level=="warning":
      warning(data)
    else:
      info(data)
def dictConvert(fromDict,toDict,CONVERSIONS):
  for key, value in fromDict.items():
    if key in CONVERSIONS:
      setattr(toDict, key, CONVERSIONS[key](value))
    else:
      setattr(toDict, key, value)
def args2dict(CONVERSIONS,**kwargs):
  info = {}
  for key in kwargs:
    if key in CONVERSIONS:
      info[key] = CONVERSIONS[key](kwargs[key])
    else:
      info[key] = kwargs[key]
  return info
def obj2jsonFile(obj,file,sort_keys=True,indent=None):
  return json.dump(obj,file,default=lambda o:o.__dict__,sort_keys=sort_keys,indent=indent)
def obj2json(obj,sort_keys=True,indent=None):
  return json.dumps(obj,default=lambda o:o.__dict__,sort_keys=sort_keys,indent=indent)
def obj2dict(obj,sort_keys=True,indent=None):
  return json.loads(obj2json(obj,sort_keys=sort_keys,indent=indent))
  
class CommonThread(threading.Thread):
  def __init__(self,func,args):
   super(CommonThread,self).__init__()        
   self.func  = func
   self.args  = args
   self.result = None
  def run(self):
    self.result = self.func(*self.args)
  def setEvent(self,event):
    self.event = event
  def eventSet(self):
    self.event.set()
  def eventClear(self):
    self.event.clear()
  @property
  def eventIsSet(self):
    return self.event.isSet()
  
  def getResult(self):
    return self.result

class CommonProcess(multiprocessing.Process):
  def __init__(self,name,func,event,args):
    super(CommonProcess,self).__init__(name=name)
    self.func  = func
    self.event = event
    self.args  = args
    self.result = None
  def run(self):
    self.result = self.func(*self.args)
  def setEvent(self,event):
    self.event = event
  def getResult(self):
    return self.result

def getPlatform():
  _system =platform.system()     
  _arch = platform.machine()
  