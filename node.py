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

import threading
import time
import random
import copy
import pickle

import traceback
import globalVar as _global

import pymongo

class Node(object):
  def __init__(self,dict):
    Node.logger = logger.logger
    _global.set("node",self)
    self.kadServer=dict.get("kadServer")
    self.socketio =None #dict.get("socketio")
    self.socketioClient = None #dict.get("socketioClient")
    self.host=dict.get("host")
    self.port=dict.get("port")
    self.isMining=False
    self.isBlockSyncing=False
    self.isolateUTXO=None
    self.isolatePool=[]
    self.tradeUTXO = None
    self.clientsNode={}
    
    self.me = dict.get("me")
    self._syncConfigFile("me")
    
    self.entryNode=dict.get("entryNode")
    self._syncConfigFile("entryNode")
        
    self.db=dict.get("db")
    self._syncConfigFile("db")
    dbhost,other=self.db.split(':')
    dbport,database=other.split('/')
    self.dbclient=pymongo.MongoClient(host=dbhost,port=int(dbport))
    self.database=self.dbclient[database]

    self.peers=None
    self._syncConfigFile("peers")
    self.nodes=set(self.peers.split(';'))
    
  def _syncConfigFile(self,config):
    if getattr(self,config) == None:
      try:
        with open(config,"r") as f:
          setattr(self,config,f.read())
      except:
        if config in ["me","db","entryNode"]:
          raise Exception("you must define {} argument use --{}".format(config,config))
        elif config=="peers":
          self.peers = self.me
        else: 
          pass
    else:
      with open(config,"w") as f:
        f.write(getattr(self,config))
    
  def setSocketio(self,socketio,socketioClient):
    self.socketio = socketio
    self.socketioClient = socketioClient
  def checkNodes(self):
    utils.warning(time.time(),"mark")
    threading.Timer(60,self.checkNodes).start()
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
    #self.checkNodes()
    doneNodes=self.nodes
    todoNodes=set()
    todoNodes.add(self.entryNode)
    if self.entryNode != None :
      while len(todoNodes):
        node = todoNodes.pop()  
        try:
          res = requests.get("http://"+node+"/node/register",params={"newNode":self.me},timeout=3)
          comeinNodes=set(res.json()["nodes"])
          doneNodes.add(node)
          todoNodes=(todoNodes | comeinNodes) - doneNodes
        except Exception as e:
          Node.logger.critical(node)
      self.nodes =  doneNodes 
      Node.logger.info("nodes:{}".format(doneNodes))
      self.save()
    
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
    
  #sync nodes,chain,blocks,transactions
  def syncLocalChain(self):
    localChain = Chain([])
    #We're assuming that the folder and at least initial block exists
    if os.path.exists(CHAINDATA_DIR):
      fileset=glob.glob(
         os.path.join(CHAINDATA_DIR, '*.json'))
      fileset.sort()
      for filepath in fileset:
        with open(filepath, 'r') as blockFile:
          try:
            blockDict = json.load(blockFile)
          except:
            Node.logger.error(filepath+" error!")
            return localChain
          localBlock = Block(blockDict)
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
    event = threading.Event()
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
    #We're assuming that the folder and at least initial block exists
    if os.path.exists(BROADCASTED_TRANSACTION_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_TRANSACTION_DIR, '*.json'))
      fileset.sort()
      for filepath in fileset:
        with open(filepath, 'r') as txFile:
          try:
            txPoolDict = json.load(txFile)
          except:
            Node.logger.error("error on:{}".format(filepath))
          txPool.append(
            Transaction.parseTransaction(txPoolDict))
    return txPool
  def txPoolRemove(self,block):
    #remove transactions in txPool
    if block:
      for TX in block.data:
        if TX.isCoinbase():
          continue
        f = str(TX.timestamp)+"_"+TX.hash+".json"
        txFile= os.path.join(BROADCASTED_TRANSACTION_DIR,f)
        try:
          os.remove(txFile)
          Node.logger.warn("del:{}".format(txFile))
        except:
          Node.logger.warn("del file not found:{}".format(txFile))
          pass
  def blockPoolSync(self):
    maxindex = self.blockchain.maxindex()
    Node.logger.info("is BlockSyning {} from pool".format(maxindex+1))
    if os.path.exists(BROADCASTED_BLOCK_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(maxindex+1)))
      for filepath in fileset:
      #if fileset:
        #filepath = fileset[0]
        with open(filepath, 'r') as blockFile:
          try:
            blockDict = json.load(blockFile)
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
                  Node.logger.debug("syncblock4.remove file {}".format(filepath))
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
            Node.logger.error("error on:{}".format(filepath))
          finally:
            lastblock = self.blockchain.lastblock()
            Node.logger.info("current blockchain high:{}-{}".format(lastblock.index,lastblock.nonce))
    Node.logger.info("end blocksync")
  def resolveFork(self,forkBlock):
    blocks=[forkBlock]
    index = forkBlock.index - 1
    Node.logger.info("fork0.begin resolveFork,fork is {}-{}".format(blocks[0].index,blocks[0].nonce))
    while True :
      fork=blocks[-1]
      fileset=glob.glob(
           os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(index)))
      i=-1
      if len(fileset)==0:
        Node.logger.info("not find prev block #{} in blockPool".format(index))
        url="http://{}/blockchain/get/{}/{}".format(self.me,self.entryNode,index)
        Node.logger.critical("resolveForm",url)
        utils.CommonThread(self.httpProcess,(url))
        break
      recursion=False
      for i,filepath in enumerate(fileset):
        with open(filepath,'r') as blockFile:
          block = Block(json.load(blockFile))
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
      
      #pNewTXdict = pickle.dumps(newTXdict)
      #self.kadServer.set("TX"+newTX.hash,pNewTXdict)
      '''
      for peer in self.nodes:
        try:
          res = requests.post("http://%s/transacted"%peer,
                         json=newTXdict,timeout=10)
          if res.status_code == 200:
            Node.logger.info("%s successed."%peer)
          else:
            Node.logger.error("%s error is %s"%(peer,res.status_code))
        except Exception as e:
          Node.logger.error("%s error is %s"%(peer,e))  
      '''
      # use socket to broadcast instead of http
      data={"source":self.me,"type":"newTX","value":newTXdict}
      Node.logger.info("broadcast transaction {}".format(newTX.hash))
      self.broadcast(data)
      
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
    Node.logger.info("end mine.",index)
    #remove transaction from txPool
    self.txPoolRemove(newBlock) 
    
    blockDict = utils.obj2dict(newBlock)
    
    #push to blockPool
    self.mined(blockDict)
    
    #broadcast to peers
    '''
    #this way is use http with self.nodes loop.It may be not efficiency
    for peer in self.nodes:
      if peer == self.me:
        continue
      try:
        res = requests.post("http://%s/mined"%peer,
                            json=blockDict,timeout=10)
      except Exception as e:
        Node.logger.error("%s error is %s"%(peer,e))  
      else:
        Node.logger.info("%s_%s success send to %s"%(index,nonce,peer))
    '''
    #new way use socketio to broacdcast 
    #print("1.local client send to entry server")
    data = {"source":self.me,"type":"newBlock","value":blockDict}
    Node.logger.info("broadcast block {}-{}".format(index,nonce))
    self.broadcast(data)
      
    Node.logger.info("mine广播完成")
    
    #以下由blockPoolSync处理
    #newBlock.save()
    #self.blockchain.add_block(newBlock)
    #self.updateUTXO(newBlock)
    
    return newBlock
  
  def findNonce(self,newBlock):
    Node.logger.info("mining for block %s" % newBlock.index)
    newBlock.updateHash()#calculate_hash(index, prev_hash, data, timestamp, nonce)
    newBlock.diffcult = NUM_ZEROS
    while str(newBlock.hash[0:NUM_ZEROS]) != '0' * NUM_ZEROS:
      #if not genesis and blockchain had updated by other node's block then stop
      if newBlock.index!=0: 
        #if self.blockchain.maxindex() >= newBlock.index:
        fileset=glob.glob(
         os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(newBlock.index)))
        if len(fileset)>=1:
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
      index = block.index
      nonce = block.nonce
      filename = BROADCASTED_BLOCK_DIR + '%s_%s.json' % (index, nonce)
      with open(filename, 'w') as f:
        utils.obj2jsonFile(block, f, sort_keys=True)
      self.database["blockchain"].insert(utils.obj2dict(block,sort_keys=True))
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
        TXhash = TX.hash
        TXtimestamp = TX.timestamp
        filename = BROADCASTED_TRANSACTION_DIR + '%s_%s.json' % (TXtimestamp,TXhash)
        with open(filename, 'w') as f:
          utils.obj2jsonFile(TX,f,sort_keys=True)
        self.database["transaction"].insert(utils.obj2dict(TX,sort_keys=True))
        #handle isolatePool
        isolatePool = copy.copy(self.isolatePool) 
        for isolateTX in isolatePool:
          if self.isolateUTXO.updateWithTX(isolateTX,utxoSet):
            self.isolatePool.remove(isolateTX)
            #save to file to transaction pool
            TXhash = isolateTX.hash
            TXtimestamp = isolateTX.timestamp
            filename = BROADCASTED_TRANSACTION_DIR + '%s_%s.json' % (TXtimestamp,TXhash)
            with open(filename, 'w') as f:
              utils.obj2jsonFile(isolateTX,f,sort_keys=True)
            self.database["transaction"].insert(utils.obj2dict(isolateTX,sort_keys=True))
          else:
            utxoSet = copy.deepcopy(self.isolateUTXO.utxoSet)
      else:
        self.isolatePool.append(TX)
      return True
    else:
      #ditch it
      utils.warning("transaction is not valid,hash is:",TX.hash)
      return False

  def broadcast(self,data):
    if self.socketioClient and self.socketioClient.client:
      self.socketioClient.client.emit("entryServer",data,namespace='/pub')
    #print('2.local server broadcast to follower client')
    self.socketio.emit("broadcast",data,namespace='/pub')

  def handleData(self,data):
    if data.get("type")=="newBlock":
      self.mined(data.get("value"))
    elif data.get("type")=="newTX":
      self.transacted(data.get("value"))
    elif data.get("type")=="setKV":
      pass
    elif data.get("type")=="getKV":
      pass