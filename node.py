import os
import json
import urllib.parse as urlparse
import requests
import datetime as date
import glob

from config import *
import logger

import utils

from chain import Chain,UTXO
from block import Block
from transaction import Transaction
from wallet import Wallet

from threading import Timer,Event

import time
import random
import copy
import pickle

import traceback
import globalVar as _global

import pymongo
from kademlia import DHT

from network import SocketioClient,PubNamespace


class ClientNS(PubNamespace):
  node = None
  def initialize(self):
    print("^"*80)
    self.node = ClientNS.node
  def on_getNodesResponse(self,*args):
    print("on_getNodesResponse",args[0])
    self.node.nodes=self.node.nodes.union(args[0])
  def on_getBlocksResponse(self,*args):
    print("on_getBlocksResponse",type(args[0]))
    for blockDict in args[0]:
      block=Block(blockDict)
      print("block:{}-{}".format(block.index,block.nonce))
      if block.isValid():
        block.saveToPool()
  def on_connect(self,*args):
    print("[Connected to new server]")
  def on_disconnect(self):
    self.node.socketioClient.disconnect()
    self.node.entryNodes=[]
    print("[Disconnected from new server]")
  def on_error(self,*data):
    print("error1:",data,self.node.socketioClient.client)
  def on_testResponse(self,*args):
    print("[",args,self.node.entryNode,"]")
  def on_broadcast(self,*args):
    print("7.sync from entryNode ")
    self.node.handleData(args[0])
    self.node.socketio.emit("broadcast",args)
  def on_localServerResponse(self,*args):
    print("8.geted from me",args)
  def on_resetEntryNodes(self,*args):
    Node.logger.info("resetEntryNodes getData:{}".format(args[0]))   
    self.node.entryNodes = args[0]
    entryNodes=list(args[0])
    entryNodes.append(self.node.me)
    self.node.socketio.emit("resetEntryNodes",entryNodes)

class Node(object):
  def __init__(self,dict):
    Node.logger = logger.logger
    _global.set("node",self)
    self.socketio =None #dict.get("socketio")
    self.socketioClient = None #dict.get("socketioClient")
    self.eMining=Event()
    self.eBlockSyncing=Event()
    self.isolateUTXO=None
    self.isolatePool=[]
    self.tradeUTXO = None
    self.clientNodes={}
    
    self.httpServer = dict.get("httpServer")
    self.me = dict.get("me")
    self.entryNode = dict.get("entryNode")
    self.entryKad = dict.get("entryKad")
    self.db = dict.get("db")
    self.peers = dict.get("peers")
    self.entryNodes = set()
    self.connected=Event()

    kadhost,kadport = self.entryKad.split(':')
    self.dht = DHT("0.0.0.0",int(kadport),boot_host=kadhost,boot_port=int(kadport))
    
    dbhost,other=self.db.split(':')
    dbport,database=other.split('/')
    self.dbclient=pymongo.MongoClient(host=dbhost,port=int(dbport))
    try:
      # The ismaster command is cheap and does not require auth.
      self.dbclient.admin.command('ismaster')
    except:
      raise("DB Server not available")
    self.database=self.dbclient[database]
    _global.set("database",self.database)
    Node.logger.info("database had been set",self.database)
    
    try:
      with open(PEERS_FILE,'r') as f:
        self.peers=f.read()
    except:
      self.peers=self.me
    self.nodes=set(self.peers.split(';'))
    
    self.otherMind=False

  def setSocketio(self,socketio):
    self.socketio = socketio
    ClientNS.node=self
    if self.entryNode != self.me: 
      self.socketioClient=SocketioClient(self.entryNode,ClientNS,'',self.me)
    else:
      self.socketioClient=None
    connected=self.connectEntryNode(self.entryNode)
    print("[connected]",connected)
    self.checkNodes = utils.CommonThread(self.checkConnectedNode,())
    self.checkNodes.setDaemon(True)
    self.checkNodes.start()
    if not connected:
      Node.logger.critical("wait for confirm connected.")
      self.connected.wait()
  def connectEntryNode(self,peer):
    def fun(*data):
      self.entryNodes = set(list(data[0]))
      self.entryNodes.add(self.entryNode)
      Node.logger.info("entryNode's entryNodes:",self.entryNodes)
    try:
      if self.socketioClient and (not self.socketioClient.connected):
        print("start connect to {}".format(peer))
        self.entryNode=peer
        self.socketioClient.reconnect(peer)
        print("reconnect:",self.socketioClient.connected)
        if self.socketioClient.connected:
          self.socketioClient.emit("getEntryNodes",{},callback=fun)
          #self.me can not in self.entryNodes 
          print("peer:{},self.me:{},entryNodes:{}".format(peer,self.me,self.entryNodes))
          if self.me in self.entryNodes:
            Node.logger.info("refuse entry node {} because it is in {}".format(peer,self.entryNodes))
            self.entryNode=None
            self.entryNodes=set()
            self.socketioClient.disconnect()
          elif len(self.entryNodes)>=3:
            Node.logger.info("refuse entry node {} because it is to be too deep level of {}".format(peer,self.entryNodes))
            self.entryNode=None
            self.entryNodes=set()
            self.socketioClient.disconnect()
          else:
            Node.logger.info("accept this entry node",peer)
            entryNodes = list(self.entryNodes)
            entryNodes.append(self.me)          
            self.socketio.emit("resetEntryNodes",entryNodes)
            utils.updateYaml("../"+CONFIG_FILE,"blockchain",{"entryNode":self.entryNode})
        else:
          self.entryNode=self.me 
    except Exception as e:
      Node.logger.critical("connect to {} error".format(peer))   
    if self.socketioClient:
      return self.socketioClient.connected
    else:
      return False   
  def checkConnectedNode(self):
    peers = list(self.nodes)
    try:
      peers.remove(self.me)
    except:
      pass
    temp=[]
    while True:
      try:
        if self.socketioClient and ((not self.socketioClient.connected) or (not self.entryNodes)):
          print("start check nodes {}".format(peers))
          self.connected.clear()
          for i,peer in enumerate(peers):
            self.connectEntryNode(peer)
            if self.socketioClient.connected:
              temp.insert(0,peer)
              temp.extend(peers[i+1:])
              self.connected.set()
              break
            elif self.entryNode == None:
              #can connect but been refused
              temp.insert(0,peer)
            elif self.entryNode == self.me:
              temp.append(peer)
            else:
              print("???",self.entryNode,self.me)
              temp.append(peer)
          else:
            Node.logger.critical("no fit entryNode to be selected!")
          peers=list(temp)
          temp=[]
          print("end check nodes {}".format(peers))
        else:
          self.connected.set()
      except Exception as e:
        Node.logger.critical("checkNodes error",e)
      time.sleep(30)
  def getRandom(self,percent):
    #find n% random nodes without me 
    if percent<0 or percent>1:
      return []
    nodes=list(self.nodes)
    try:
      nodes.remove(self.me)
    except:
      pass
    cnt = round(len(nodes)*percent)
    nodes = random.sample(nodes,cnt)  
    return nodes
    
  def syncOverallNodes(self):    
    def fun(*data):
      print("!!",data,self.me)
    Node.logger.debug("step one: get entryNode's nodes")
    if self.socketioClient and self.socketioClient.client:
      self.socketioClient.emit('test','hello',callback=fun) 
      self.socketioClient.emit("getNodes",{},)
    Node.logger.debug("step two: broadcast self.me")
    Node.logger.info("register node {}".format(self.me))
    self.broadcast(self.me,type="registeNode")
    self.save()
    return
  def register(self,newNode):
    self.nodes.add(newNode)
    self.save()
    return self.nodes
    
  def save(self):
    with open("peers",'w') as f:
      peers=";".join(self.nodes)
      f.write(peers)
            
  def unregister(self,delNode):
    try:
      self.nodes.remove(delNode)
      self.save()
    except:
      pass
    return self.nodes
    
  #clear transaction on node start
  def clearTransaction(self):
    self.database["transaction"].remove({})  
  #sync nodes,chain,blocks,transactions
  def syncLocalChain(self):
    localChain = Chain([])
    for block in self.database["blockchain"].find({},{"_id":0}).sort([("index",1)]):
      localBlock=Block(block)
      localChain.addBlock(localBlock)
    return localChain

  def httpProcess(self,url,timeout=3,cb=None,cbArgs=None):
    try:
      result = {"url":url,"response":{}}
      peer = urlparse.urlsplit(url).netloc
      res = requests.get(url,timeout=timeout)
      try:
        if cb:
          result = cb(res,url,cbArgs)
        else:
          result = {"url":url,"response":res}
      except Exception as e:
        utils.danger("error on execute ",cb.__name__,e)
        raise e
    except requests.exceptions.ConnectionError:
      Node.logger.warn("Peer at %s not running. Continuing to next peer." % peer)
    except requests.exceptions.ReadTimeout:
      Node.logger.warn("Peer at %s timeout. Continuing to next peer." % peer)
    except Exception as e:
      Node.logger.error("Peer at %s error."% peer)
    else:
      Node.logger.info("Peer at %s is running. " % peer)
    return result
    
  def peerHttp(self,path,timeout=3,cb=None,percent=1,nodes=[],*cbArgs):
    if nodes==[]:
      nodes = self.getRandom(percent)
    threads=[]
    event = Event()
    for i,peer in enumerate(nodes):
      slash = '/' if path[0]!='/' else ''
      if type(path)==str:
        url = "http://"+peer+slash+path
      elif type(path)==list:
        length=len(path)
        url = "http://"+peer+slash+path[i%length]
      else:
        url = "http://"+peer
      threads.append(utils.CommonThread(
          self.httpProcess,
          (url,timeout,cb,cbArgs)))
      Node.logger.info(url)
    for j in threads:
      j.setDaemon(True)
      j.start()
    for j in threads:
      j.join()
    result=[]
    for k in threads:
      result.append(k.getResult())
    return result  
                   
  def syncToBlockPool(self,nodes,fromIndex,toIndex):
    def callback(res,url,cbArgs):
      if type(res.json())==list:
        try:
           blocks=[Block(bdict) for bdict in res.json()]
           for block in blocks:
             if block.isValid():
               block.saveToPool()
        except:
           Node.logger.error("error on syncRangeChain",traceback.format_exc())

    cnt = len(nodes)
    res="nodes=[]"
    if cnt>0:
      step = (toIndex - fromIndex + 1) // cnt
      path = []
      begin = fromIndex
      end = fromIndex + step - 1
      if end<0: end=0
      for i in range(cnt):
        path.append("blockchain/{}/{}".format(begin,end))
        begin = end +1
        end = begin+step - 1
        if i==cnt - 2 and end < toIndex:
          end = toIndex
      res = self.peerHttp(path,3,callback,1,nodes,"test")
    return res
    
  def syncOverallChain(self,full=False):
    def getHighestNodes(res,url,cbArgs):
      bestIndex = cbArgs[0]
      if res.status_code!=200:
        return {}
      resIndex = int(res.text)
      if resIndex > bestIndex:
        bestIndex=resIndex
        peer = urlparse.urlsplit(url).netloc
      else:
        return {}
      return {"url":url,"bestIndex":bestIndex,"peer":peer}

    bestChain = self.syncLocalChain()
    if full:
      localIndex = -1
    else:
      localIndex = bestChain.maxindex() - NUM_FORK
      if localIndex < 0 :
        localIndex = -1
    bestIndex = localIndex 
    nodes=[]
    
    Node.logger.debug("setp1:get highest nodes list")
    path = '/blockchain/maxindex'
    result = self.peerHttp(path,3,getHighestNodes,1,[],bestIndex)
    Node.logger.info("getHighestNodes1:{}".format(result)) 
    for i,peer in enumerate(result): 
      if "bestIndex" in peer:
        if peer["bestIndex"]>bestIndex:
          bestIndex=peer["bestIndex"]
          nodes=[]
          nodes.append(peer["peer"])
        elif peer["bestIndex"] == bestIndex:
          nodes.append(peer["peer"])
    Node.logger.info("getHightestNodes2:{}".format(nodes))
    
    Node.logger.debug("step2:put range block into blockPool from each node")
    fromIndex = localIndex + 1 
    if fromIndex<0:
      fromIndex = 0
    self.syncToBlockPool(nodes,fromIndex,bestIndex) 
    Node.logger.debug("step3:wait blockPoolSync to build a bestChain")
    self.blockchain = bestChain
    
    return bestIndex
      
  def resetUTXO(self):
    self.blockchain.utxo.reset(self.blockchain)
    #定义tradeUTXO,避免与blockchain的UTXO互相影响，更新trade时会更新tradeUTXO，以保证多次交易。更新block时使用blockchain下的UTXO
    Node.logger.critical("resetUTXO!!!")
    self.tradeUTXO = UTXO("trade")
    self.tradeUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
    self.isolateUTXO = UTXO("isolate")
    self.isolateUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
    return self.blockchain.utxo.utxoSet
  
  def updateUTXO(self,newblock):
    Node.logger.critical("updateUTXO!!!")
    if self.blockchain.utxo.update(newblock):
      self.tradeUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
      self.isolateUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
      return True
    else:
      return False
  def txPoolSync(self):
    txPool=[]
    for txDict in self.database["transaction"].find({},{"_id":0}).sort([("timestamp",1)]):
      txPool.append(Transaction.parseTransaction(txDict))
    return txPool
  def txPoolRemove(self,block):
    #remove transactions from txPool
    if block:
      try:
        for TX in block.data:
          if TX.isCoinbase():
            continue
          self.database["transaction"].remove({"hash":TX.hash})
      except Exception as e:
        Node.logger.critical(block,e)
        raise e
  def blockPoolSync(self):
    maxindex = self.blockchain.maxindex()
    Node.logger.info("is BlockSyning {} from pool".format(maxindex+1))
    for blockDict in self.database["blockpool"].find({"index":maxindex+1},{"_id":0}):
      try:
        block = Block(blockDict)
        if block.isValid():
          Node.logger.debug("syncblock0.current maxindex {}".format(self.blockchain.maxindex()))
          if self.blockchain.addBlock(block):
            if block.index==0:
              doutxo = self.resetUTXO()
            else:
              doutxo = self.updateUTXO(block)
            Node.logger.debug("syncblock1.after update utxo {},and this fun is {}".format(self.blockchain.utxo.getSummary(),doutxo))
            if doutxo:
              Node.logger.debug("syncblock2. txPoolRemove".format(block.index))
              self.txPoolRemove(block)
              Node.logger.debug("syncblock3.block.save")
              block.save()
              Node.logger.debug("syncblock4.remove pool block {}".format(block.index))
              block.removeFromPool()
              Node.logger.debug("syncblock5.current maxindex {}".format(self.blockchain.maxindex()))
              break
            else:
              self.blockchain.blocks.pop() #del added block just moment
              if self.resolveFork(block):
                break
          else:
            if self.resolveFork(block):
              break
      except Exception as e:
        Node.logger.critical(traceback.format_exc())
        #Node.logger.error("error on:{}".format(filepath))
      finally:
        lastblock = self.blockchain.lastblock()
        Node.logger.info("current blockchain high:{}-{}".format(lastblock.index,lastblock.nonce))
    Node.logger.info("end blocksync {}-{}".format(lastblock.index,lastblock.nonce))
  def resolveFork(self,forkBlock):
    blocks=[forkBlock]
    index = forkBlock.index - 1
    Node.logger.info("fork0.begin resolveFork,fork is {}-{}".format(blocks[0].index,blocks[0].nonce))
    while True :
      fork=blocks[-1]
      fileset = [item for item in self.database["blockpool"].find({"index":index},{"_id":0})]
      i=-1
      if len(fileset)==0:
        Node.logger.info("not find prev block #{} in blockPool".format(index))
        url="http://{}/blockchain/get/{}/{}".format(self.me,self.entryNode,index)
        Node.logger.critical("resolveForm",url)
        utils.CommonThread(self.httpProcess,(url))
        break
      recursion=False
      for i,blockDict in enumerate(fileset):
        block = Block(blockDict)
        Node.logger.info("fork1.poolblock {}-{} isValid?".format(block.index,block.nonce))  
        if block.isValid():
          Node.logger.info("fork2.forkblock({}-{}) can link poolblock({}-{})?".format(fork.index,fork.nonce,block.index,block.nonce))
          if fork.prev_hash != block.hash:
            continue
          if index>0:
            Node.logger.critical(index,block.index,'-',block.nonce)
            Node.logger.info("fork3.poolblock({}-{}) can link blockchain({}-{})?".format(block.index,block.nonce,self.blockchain.findBlockByIndex(index - 1).index,self.blockchain.findBlockByIndex(index - 1).nonce))
          else:
            Node.logger.info("fork3.poolblock({}-{}) isGenesisblock?".format(block.index,block.nonce,index))
          blocks.append(block) 
          if index==0 or block.prev_hash == self.blockchain.findBlockByIndex(index - 1).hash:
            #done,replace blocks in blockchain,move correspondent into blockPool
            Node.logger.info("forkstep1> move correspondent into blockPool")
            index = block.index - 1
            
            for b in blocks[1:]:
              idx = b.index
              Node.logger.debug("fork6.moveBlockToPool {}-{}".format(idx,self.blockchain.blocks[idx].nonce))
              self.blockchain.moveBlockToPool(idx) 
              
            Node.logger.info("forkstep2> add new blocks")
            blocks.reverse()
            for b in blocks:
              Node.logger.info("fork8.addblock {}-{}".format(b.index,b.nonce))
              if self.blockchain.addBlock(b):
                Node.logger.info("fork9.UTXO")
                if b.index==0:
                  doutxo=self.resetUTXO()
                else:
                  doutxo=self.updateUTXO(b)
                if doutxo:
                  Node.logger.info("fork10.txPoolRemove")
                  self.txPoolRemove(b)
                  Node.logger.info("fork11.save")
                  b.save()
                  Node.logger.info("fork12.removeFromPool")
                  b.removeFromPool()
                  Node.logger.info("fork13.next")
                else:
                  Node.logger.info("utxo error!")
                  self.blockchain.blocks.pop()
                  return True
            return True
          else:
            index = block.index - 1 
            Node.logger.info("fork4.nextblock {}".format(index))
            recursion=True
            break
      if i==len(fileset) - 1 and not recursion:
        Node.logger.info("fork14.find prev block in blockPool,but none can link fork block or can link main chain")
        if index==0:
          url="http://{}/blockchain/get/{}/{}".format(self.me,self.entryNode,0)
        else:        
          url="http://{}/blockchain/get/{}/{}".format(self.me,self.entryNode,index-1)
        Node.logger.critical("resolveForm",url)
        #utils.CommonThread(self.httpProcess,(url))
        break
    return False
    
  def tradeTest(self,nameFrom,nameTo,amount,script=""):
    if nameFrom=='me':
      wFrom = Wallet(self.me)
    else:
      wFrom = Wallet(nameFrom)
    if nameTo=='me':
      wTo = Wallet(self.me)
    else:
      wTo = Wallet(nameTo)
    if wFrom.key[0]:
      return self.trade(
        wFrom.key[0],wFrom.key[1],wTo.key[1],amount,script)
    else:
      return {"errCode":2,"errText":"{} have not private key on this node".format(nameFrom)}
  def trade(self,inPrvkey,inPubkey,outPubkey,amount,script=""):
    newTX=Transaction.newTransaction(
      inPrvkey,inPubkey,outPubkey,amount,self.tradeUTXO,script)
    newTXdict=None
    if type(newTX)==dict:
      errObj=newTX
      Node.logger.critical(errObj["errCode"],errObj["errText"])
      return errObj
    else:
      newTXdict=utils.obj2dict(newTX)
      self.transacted(newTXdict)
      # use socket to broadcast instead of http
      Node.logger.info("broadcast transaction {}".format(newTX.hash))
      self.broadcast(newTXdict,type="newTX")
      
      Node.logger.info("transaction广播完成")
      return newTXdict

  def genesisBlock(self,coinbase):
    newBlock=self.findNonce(Block(
      {"index":0,
      "prev_hash":"0",
      "data":[coinbase],
      "timestamp":date.datetime.now().strftime('%s')}))
    newBlock.save()
    
  def mine(self,coinbase):
    Node.logger.info("is Mining...")
    #sync transaction from txPool
    txPool = self.txPoolSync()  
    txPoolDict=[]
    txPoolDict.append(coinbase)
    for item in txPool:
      txPoolDict.append(utils.obj2dict(item,sort_keys=True))
    #currentChain = self.syncLocalChain() #gather last node
    #prevBlock = currentChain.lastblock()
    prevBlock = self.blockchain.lastblock()
    
    #mine a block with a valid nonce
    index = int(prevBlock.index) + 1
    timestamp = date.datetime.now().strftime('%s')
    data = txPoolDict
    prev_hash = prevBlock.hash
    nonce = 0  
    blockDict = utils.args2dict(CONVERSIONS=BLOCK_VAR_CONVERSIONS,index=index, timestamp=timestamp, data=data, prev_hash=prev_hash, nonce=nonce)
    Node.logger.info("begin mine...{}".format(index))
    newBlock = self.findNonce(Block(blockDict))
    if newBlock==None:
      Node.logger.warn("other miner mined")
      return "other miner mined"
    Node.logger.info("end mine {}-{}.".format(index,newBlock.nonce))
    #remove transaction from txPool
    self.txPoolRemove(newBlock) 
    
    blockDict = utils.obj2dict(newBlock)
    
    #push to blockPool
    self.mined(blockDict)
    
    Node.logger.info("broadcast block {}-{}".format(newBlock.index,newBlock.nonce))
    self.broadcast(blockDict,type="newBlock")
      
    Node.logger.info("mine广播完成")
    
    #以下由blockPoolSync处理
    #newBlock.save()
    #self.blockchain.add_block(newBlock)
    #self.updateUTXO(newBlock)
    
    return newBlock
  
  def findNonce(self,newBlock):
    Node.logger.info("mining for block %s" % newBlock.index)
    self.otherMined=False
    newBlock.updateHash()#calculate_hash(index, prev_hash, data, timestamp, nonce)
    newBlock.diffcult = NUM_ZEROS
    while str(newBlock.hash[0:NUM_ZEROS]) != '0' * NUM_ZEROS:
      #if not genesis and blockchain had updated by other node's block then stop
      if newBlock.index!=0 and self.otherMined: 
          return None
      newBlock.nonce += 1
      newBlock.updateHash()
    Node.logger.info("block %s mined. Nonce: %s , hash: %s" % (newBlock.index, newBlock.nonce,newBlock.hash))
    Node.logger.info("block #{} is {}".format(
          str(newBlock.index),
          newBlock.isValid()))
    return newBlock #we mined the block. We're going to want to save it
  def mined(self,blockDict):
    #validate possible_block
    block = Block(blockDict)
    Node.logger.info("recieve block index {}-{}".format(block.index,block.nonce))
    if block.isValid():
      #save to file to possible folder
      self.database["blockpool"].update({"hash":block.hash},{"$set":utils.obj2dict(block,sort_keys=True)},upsert=True)
      self.otherMined=True
      return True
    else:
      return False
  def transacted(self,txDict):
    #validate possible_block
    TX = Transaction.parseTransaction(txDict)
    Node.logger.info("recieve transaction {}".format(TX.hash))
    if TX.isValid():
      utxoSet = copy.deepcopy(self.isolateUTXO.utxoSet)
      #log.critical("1",utxoSet)
      if self.isolateUTXO.updateWithTX(TX,utxoSet):
        self.isolateUTXO.utxoSet = utxoSet
        #save to file to transaction pool
        self.database["transaction"].update({"hash":TX.hash},{"$set":utils.obj2dict(TX,sort_keys=True)},upsert=True)
        #handle isolatePool
        isolatePool = copy.copy(self.isolatePool) 
        for isolateTX in isolatePool:
          if self.isolateUTXO.updateWithTX(isolateTX,utxoSet):
            self.isolatePool.remove(isolateTX)
            #save to file to transaction pool
            self.database["transaction"].update({"hash":isolateTX.hash},{"$set":utils.obj2dict(isolateTX,sort_keys=True)},upsert=True)
          else:
            utxoSet = copy.deepcopy(self.isolateUTXO.utxoSet)
      else:
        self.isolatePool.append(TX)
      return True
    else:
      #ditch it
      utils.warning("transaction is not valid,hash is:",TX.hash)
      return False

  def broadcast(self,data,type):
    message = {"source":[self.me],"type":type,"value":data}
    print('1.send data to entryNode')
    if self.socketioClient :
      res=self.socketioClient.emit("entryServer",message)
      print("result:",res)
    print('2.local server broadcast to follower client')
    res = self.socketio.emit("broadcast",message)
    print("result:",res)

  def handleData(self,data):
    if data.get("type")=="newBlock":
      self.mined(data.get("value"))
    elif data.get("type")=="newTX":
      self.transacted(data.get("value"))
    elif data.get("type")=="registeNode":
      Node.logger.info("testBroadcast getData:{}".format(data.get("value")))      
      self.register(data.get("value"))
    elif data.get("type")=="setKV":
      pass
    elif data.get("type")=="getKV":
      pass
    elif data.get("type")=="testBroadcast":
      Node.logger.info("testBroadcast getData:{}".format(data.get("value")))