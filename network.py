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
from threading import Event
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
  def on_connect(self,*args):
    print("[Connected to server]")
  def on_disconnect(self):
    print('[Disconnected from server]')
  def on_wellcome(self,data):
    print("wellcome",data)
  def on_goodbye(self,data):
    print("goodbye",data)
  def on_myevent(self,*args):
    print("recieved from remote",args)
    with SocketIO_Client("127.0.0.1",5000,Namespace2) as socketioLocal:
      print("sync to local server")
      socketioLocal.emit("event",args)
  def on_testResponse(self,*args):
    print("[",args,"]")

  def on_broadcast(self,*args):
    #print("6.geted from entry Server",args)
    print("7.sync from local client to local server")
    socketioLocal = SocketioClient("127.0.0.1:5000",PrvNamespace,'/prv')
    socketioLocal.once("localServer",args[0],"localServerResponse",lambda arg:print(arg))
    
    #socketIO = SocketIO_Client("127.0.0.1",5000)
    #socketioLocal = socketIO.define(PrvNamespace,'/prv')
    #socketioLocal.emit("localServer",args[0])
    #socketIO.wait(seconds=1)
    
          
class PrvNamespace(BaseNamespace):
  def on_test(self,*args):
    print("11.just a test")
  def on_broadcast(self,*args):
    print("8.geted from me",args)
    
class SocketioClient(object):
  def __init__(self,entryNode,tNamespace=None,path='/',me="",params={}):
    self.host = entryNode.split(':')[0]
    self.port = int(entryNode.split(':')[1])
    self.tNamespace = tNamespace
    self.params = params
    self.path = path
    self.client = None
    self._loop = None
    self._event = Event()
    self._loopThread = None
    self.connected=False
    self.me=me
    self.params["me"]=self.me
  ###### absloate
  async def _conn(self):
    io = SocketIO_Client(self.host,self.port,params=self.params)
    self.client = io.define(self.tNamespace,self.path) 
  def _startLoop(self):
    self._loop.run_until_complete(self._conn())  
    self.client._io.wait()
    #self._client.wait_for_callbacks(seconds=1) 
    #self.loop.run_forever()
  def start(self):
    self._loop = asyncio.get_event_loop()
    self._loopThread = utils.CommonThread(self._startLoop,())
    self._loopThread.setDaemon(True)
    self._loopThread.start()
  ####### 
  def stop(self):
    if self.client:
      self.client.disconnect()
    self.connected=False 
  def once(self,emitEventname,data,respEventname=None,fun=None):
    try:
      io = SocketIO_Client(self.host,self.port,wait_for_connection=False,params=self.params)
      self.client = io.define(self.tNamespace,self.path) 
      self.client.once(respEventname,fun)
      self.client.emit(emitEventname,data)
      self.client._io.wait(seconds=1)
    except ConnectionError:
        print('The server is down. Try again later.')
        
  def _connect(self):
    try:
      self._event.clear()
      self.connected=False
      print(1)
      io = SocketIO_Client(self.host,self.port,wait_for_connection=True,params=self.params)
      print(2)
      self.client = io.define(self.tNamespace,self.path) 
      print(3)
      self.connected=True
      self._event.set()
      self.client._io.wait()
    except:
      self._event.set()
      
  def connect(self):
    self._loopThread = utils.CommonThread(self._connect,())
    self._loopThread.setDaemon(True)
    self._loopThread.start()
    if not self._event.isSet():
      print("wait a moment...")
    self._event.wait(10)
    return self.connected
  
  def reconnect(self,entryNode):
    self.stop()
    self.host = entryNode.split(':')[0]
    self.port = int(entryNode.split(':')[1])
    self._loopThread = utils.CommonThread(self._connect,())
    self._loopThread.setDaemon(True)
    self._loopThread.start()
    if not self._event.isSet():
      print("wait a moment...")
    self._event.wait(10)
    return self.connected
    
  def emit(self,emitEventName,data,callback=None):
    try:
      self.client.emit(emitEventName,data,callback=callback)   
    except:
      print("emit error")
