import requests
import urllib.parse as urlparse
import random
import hashlib
import utils
import time

from flask_socketio import Namespace,emit
from socketIO_client import SocketIO as SocketIO_Client
from socketIO_client import BaseNamespace


from requests.exceptions import ConnectionError
import asyncio
from threading import Thread,Event
import logging

#logging.getLogger('socketIO-client').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

class Gossip(object):
  def __init__(self,nodes,me):
    Gossip.logger = logger.logger
    self.nodes=list(nodes)
    try:
      self.nodes.remove(me)
    except:
      pass
    self.me = me
    self.data={}
    self.broadcastNum=1
  def cli(self,key,value):
    Gossip.logger.debug("cli",self.nodes)
    valHash = hashlib.sha256(value.encode()).hexdigest()
    self.data[key]={"todo":list(self.nodes),
                    "done":[],
                    "comein":[],
                    "feedback":False,
                    "value":value,
                    "hash":valHash}
    ok=False
    todo = self.data[key]["todo"]
    done = self.data[key]["done"]
    while not ok and todo:
      n = len(todo) if len(todo)<self.broadcastNum else self.broadcastNum
      peers = random.sample(todo,n)
      for peer in peers:
        url="http://{}/syn1/{}/{}/{}".format(
           peer,key,valHash,self.me)
        result=self.httpProcess(url)
        done.append({"peer":peer,"msg":result["msg"]})
        try:
          todo.remove(peer)
        except:
          pass
        if result["status_code"]==requests.codes.ok:
          ok=True
    self.data[key]["todo"]=todo
    self.data[key]["done"]=done
    if ok:
      return "cli success to "+str(peers)
    else:
      return "cli not success!"
  def syn1(self,key,valHash,you):
    #ack to sync data
    if key in self.data:  #
      if "hash" in self.data[key] and self.data[key]["hash"]==valHash: #have this k-v
        Gossip.logger.info("syn1","key {} has {}".format(key,self.data[key]["value"]))
        self.data[key]["comein"].append(you)
        #broadcast
        if not self.data[key]["feedback"]:
          firstComein=self.data[key]["comein"][0]
          result = self.broadcast(key,valHash,firstComein)
        else:
          result = 'ok'
      else:  #have this k but v is old
        Gossip.logger.info("syn1","key {} has old value {}".format(key,self.data[key]["value"]))
        self.data[key]["todo"]=list(self.nodes)
        self.data[key]["done"]=[]
        self.data[key]["comein"]=[you]
        self.data[key]["feedback"]=False
        self.data[key]["hash"]= valHash
        self.data[key]["value"]=None
        url="http://{}/ack/{}/{}".format(
           you,key,self.me)
        result=self.httpProcess(url)
        Gossip.logger.info("syn1","message from {} to {}".format(you,self.me))
    else: #new k-v occure
      self.data[key]={}
      self.data[key]["todo"]=list(self.nodes)
      self.data[key]["done"]=[]
      self.data[key]["comein"]=[you]
      self.data[key]["feedback"]=False
      self.data[key]["hash"]= valHash
      self.data[key]["value"]=None
      url="http://{}/ack/{}/{}".format(
           you,key,self.me)
      result=self.httpProcess(url)
      Gossip.logger.info("syn1","message from {} to {}".format(you,self.me))
    return result
  def ack(self,key,you):
    value=self.data[key]["value"]
    url="http://{}/syn2/{}/{}/{}".format(you,key,value,self.me)
    result = self.httpProcess(url)
    Gossip.logger.info('ack','put {}-{} to {}'.format(key,value,you))
    return result
  def syn2(self,key,value,you):
    if key in self.data:
      self.data[key]["value"]=value
      valHash=self.data[key]["hash"]
    Gossip.logger.info('syn2','peer {} update {}-{}'.format(self.me,key,value))
    #broadcast
    return self.broadcast(key,valHash,you)
  def broadcast(self,key,valHash,you): 
    todo=self.data[key]["todo"]
    done=self.data[key]["done"]
    comein=self.data[key]["comein"]
    try:
      todo.remove(you) 
    except:
      pass
    ok=False
    while not ok and todo:
      n = len(todo) if len(todo)<self.broadcastNum else self.broadcastNum
      peers = random.sample(todo ,n)
      for peer in peers:
        url="http://{}/syn1/{}/{}/{}".format(
           peer,key,valHash,self.me)
        result=self.httpProcess(url)
        done.append({"peer":peer,"msg":result["msg"]})
        try:
          todo.remove(peer)
        except:
          Gossip.logger.error("broadcast remove error {} {}:".format(todo,peer))
        Gossip.logger.warn('syn1 broadcast from {} to {}'.format(self.me,peers))
        if result["status_code"]==requests.codes.ok:
          ok=True
    self.data[key]["todo"]=todo
    self.data[key]["done"]=done
    self.data[key]["comein"]=comein
    if ok:
      return list(peers)
    else:
      url="http://{}/syn1/{}/{}/{}".format(
           you,key,valHash,'null'+"."+self.me)
      result=self.httpProcess(url)
      self.data[key]["feedback"]=True
      done.append({"end":1,"peer":you,"msg":result["msg"]}) 
      Gossip.logger.warn("no node to broadcast")
      return "no node to broadcast." 
  def getValue(self,key):
    if key in self.data:
      value = self.data[key]["value"]
      todo = self.data[key]["todo"]
      done = self.data[key]["done"]
      comein = self.data[key]["comein"]
      feedback=self.data[key]["feedback"]
      valHash = self.data[key]["hash"]
      return {"key":key,"value":value,"hash":valHash,"todo":todo,"done":done,"comein":comein,"feedback":feedback}
    else:
      return {"key":key,"value":None,"hash":None}
  def httpProcess(self,url,timeout=5,cb=None,cbArgs=None):
    result={"url":url}
    res={}
    try:
      peer = urlparse.urlsplit(url).netloc
      res = requests.get(url,timeout=timeout)
      try:
        if cb:
          res1 = cb(res,url,cbArgs)
          result["status_code"] = res.status_code
          result["msg"]=res.text
          result["res"]=res1 
        else:
          result["status_code"] = res.status_code
          result["msg"]=res.text
          result["res"]=res 
      except Exception as e:
        name=""
        if cb:
          name=cb.__name__
        Gossip.logger.error("error on execute {}",name)
        result["status_code"] = -1
        result["msg"]="error on execute %s"%name
        result["res"]=res 
    except requests.exceptions.ConnectionError:
      msg = "Peer at %s not running. Continuing to next peer." % peer
      Gossip.logger.warn(msg)
      result["status_code"] = -2
      result["msg"]=msg
      result["res"]=None 
    except requests.exceptions.ReadTimeout:
      msg = "Peer at %s timeout. Continuing to next peer." % peer
      Gossip.logger.warn(msg)
      result["status_code"] = -3
      result["msg"]=msg
      result["res"]=None 
    except Exception as e:
      Gossip.logger.error("Peer at %s error."% peer,e)
    else:
      Gossip.logger.info("Peer at %s is running. " % peer)
      
    return result
    
class PubNamespace(BaseNamespace):
  '''def on_open(self,*args):
    print("open occure",args)
  def on_close(self,*args):
    print("close occure",args)
  def on_ping(self,*args):
    print("ping occure",args)
  def on_pong(self,*args):
    print("pong occure",args)
  '''
  def on_connect(self,*args):
    print("[Connected to server]")
  def on_disconnect(self):
    print('[Disconnected from server]')
  def on_wellcome(self,*args):
    print("wellcome",args)
  def on_goodbye(self,*args):
    print("goodbye",args)
  def on_error(self,*args,**kv):
    print("error",args,kv)
  def on_testResponse(self,*args):
    print("[",args,"]")
    
class SocketioClient(object):
  def __init__(self,entryNode,tNamespace=None,path='',me="",peers=[],params={}):
    self.entryNode = entryNode
    self.entryNodes = []
    self.host = entryNode.split(':')[0]
    self.port = int(entryNode.split(':')[1])
    self.tNamespace = tNamespace
    self.params = params
    self.path = path
    self.thread = None
    self.client = None
    self.connected=False
    self.connecting=Event()
    self.me=me
    self.params["me"]=self.me
    self.peers=set(peers) - set([me])
  def disconnect(self):
    if self.client and self.connected:
      self.client.disconnect()
    self.connected=False 
  def once(self,emitEventname,data,respEventname=None,fun=None):
    try:
      io = SocketIO_Client(self.host,self.port,wait_for_connection=False,params=self.params)
      self.client = io.define(self.tNamespace,self.path) 
      self.client.once(respEventname,fun)
      self.emit(emitEventname,data)
    except:
        print('The server is down. Try again later.')
  def _connect(self):
    self.connecting.clear()
    try:
      self.connected=False
      io = SocketIO_Client(self.host,self.port,wait_for_connection=False,params=self.params)
      self.client = io.define(self.tNamespace,self.path) 
      self.connected=True
      io.wait()
    except Exception as e:
      self.disconnect()
      print("error to connect entryNode:{}".format(self.entryNode))
    self.connecting.set()
    print("close thread")      
  def connect(self):
    self.thread = utils.CommonThread(self._connect,())
    self.thread.setDaemon(True)
    self.thread.start()
    self.connecting.wait(5)

  def reconnect(self,entryNode):
    self.disconnect()
    self.entryNode = entryNode
    self.host = entryNode.split(':')[0]
    self.port = int(entryNode.split(':')[1])
    self.connect()
    
  def emit(self,emitEventName,data,path='/',callback=None):
    try:
      if not self.connected or not self.client:
        return False
      self.client.path=path
      self.client.emit(emitEventName,data,callback=callback)   
      self.client._io.wait(1)
      return True
    except Exception as e:
      return False