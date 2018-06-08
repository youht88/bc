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
from wallete import Wallete

import threading
import time
import random
import copy

import traceback

class Node(object):
  def __init__(self,dict):
    Node.logger = logger.logger
    print('*'*40,Node.logger)
    self.me = dict["me"]
    self.entryNode=dict["entryNode"]
    self.host=dict["host"]
    self.port=dict["port"]
    self.isMining=False
    self.isBlockSyncing=False
    #fetch me node 
    if self.me == None:
      try:
        with open(ME_FILE,"r") as f:
          self.me = f.read()
      except:
        raise Exception("if not define --me,you must define it in me file named by ME_FILE")
    else:
      with open(ME_FILE,"w") as f:
        f.write(self.me)
    #fetch entry node     
    if self.entryNode == None:
      try:
        with open(ENTRYNODE_FILE,"r") as f:
          self.entryNode = f.read()
      except:
        pass
    else:
      with open(ENTRYNODE_FILE,"w") as f:
        f.write(self.entryNode)
    
    #fetch local peers to load nodes
    self.nodes=set()
    self.peersFile=PEERS_FILE
    try:
      with open(self.peersFile,"r") as f:
        items = f.readlines()
        for item in items:
          self.nodes.add(item[:-1])
    except:
      pass
    if len(self.nodes)==0:
      self.nodes.add(self.me)
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
          Node.logger.critical(node,traceback.format_exc())
      self.nodes =  doneNodes 
      Node.logger.info("nodes:{}".format(doneNodes))
      self.save()
    
  def register(self,newNode):
    self.nodes.add(newNode)
    self.save()
    return self.nodes
    
  def save(self):
    with open(self.peersFile,'w') as f:
      nodes=[item+'\n' for item in self.nodes]
      f.writelines(nodes)
            
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
    
  def peerHttp(self,path,timeout,cb,percent=1,nodes=[],*cbArgs):
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
      try:
         blocks=[Block(bdict) for bdict in res.json()]
         for block in blocks:
           if block.isValid():
             block.saveToPool()
      except:
         Node.logger.error("error on syncRangeChain")

    cnt = len(nodes)
    res="nodes=[]"
    if cnt>0:
      step = (toIndex - fromIndex + 1) // cnt
      path = []
      begin = fromIndex
      end = fromIndex + step - 1
      for i in range(cnt):
        path.append("blockchain/{}/{}".format(begin,end))
        begin = end +1
        end = begin+step - 1
        if i==cnt - 2 and end < toIndex:
          end = toIndex
      res = self.peerHttp(path,3,callback,1,nodes,"test")
    return res
    
  def syncOverallChain(self,full=False):
    bestChain = self.syncLocalChain()
    if full:
      localIndex = -1
    else:
      localIndex = bestChain.maxindex() - NUM_FORK
      if localIndex < 0 :
        localIndex = -1
    bestIndex = localIndex 
    nodes=[]
    
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
    self.blockchain.utxo = UTXO()
    self.blockchain.utxo.reset(self.blockchain)
    #定义tradeUTXO,避免与blockchain的UTXO互相影响，更新trade时会更新tradeUTXO，以保证多次交易。更新block时使用blockchain下的UTXO
    self.tradeUTXO = UTXO()
    self.tradeUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
    return self.blockchain.utxo.utxoSet
  
  def updateUTXO(self,newblock):
    self.blockchain.utxo.update(newblock)
    self.tradeUTXO.utxoSet = copy.deepcopy(self.blockchain.utxo.utxoSet) 
    
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
              Node.logger.debug("syncblock0.maxindex {}".format(self.blockchain.maxindex()))
              if self.blockchain.addBlock(block):
                Node.logger.debug("syncblock1. txPoolRemove".format(block.index))
                self.txPoolRemove(block)
                Node.logger.debug("syncblock2.block.save")
                block.save()
                Node.logger.debug("syncblock3.remove file {}".format(filepath))
                os.remove(filepath)
                Node.logger.debug("syncblock4.befor update utxo {}".format(self.blockchain.maxindex()))
                self.updateUTXO(block)
                Node.logger.debug("syncblock5.after update utxo {}".format(self.blockchain.utxo.getSummary()))
                break
              else:
                if self.resolveFork(block):
                  break
          except Exception as e:
            Node.logger.critical(traceback.format_exc())
            Node.logger.error("error on:{}".format(filepath))
          finally:
            Node.logger.info("current blockchain high:{}".format(self.blockchain.maxindex()))
    Node.logger.info("end blocksync")
  def resolveFork(self,forkBlock):
    blocks=[forkBlock]
    index = forkBlock.index - 1
    self.logger.info("fork0.begin resolveFork {} {}".format(blocks[0].index,index))
    while True :
      fork=blocks[-1]
      fileset=glob.glob(
           os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(index)))
      i=-1
      if len(fileset)==0:
        Node.logger.info("not find prev block in blockPool {}".format(index))
        break
      recursion=False
      for i,filepath in enumerate(fileset):
        with open(filepath,'r') as blockFile:
          block = Block(json.load(blockFile))
          Node.logger.info("fork1.test block.isValid")
          if block.isValid():
            Node.logger.info("fork2.test fork.prev_hash == block.hash")
            if fork.prev_hash != block.hash:
              continue
            Node.logger.info("fork3.test block.prev_hash can link blockchain {} {}".format(block.prev_hash,self.blockchain.findBlockByIndex(index - 1).hash))
            blocks.append(block) 
            if index==0 or block.prev_hash == self.blockchain.findBlockByIndex(index - 1).hash:
              #done,replace blocks in blockchain,move correspondent into blockPool
              Node.logger.info("forkstep1> move correspondent into blockPool")
              index = block.index - 1
              
              for b in blocks[1:]:
                Node.logger.info("fork6.b.index {}".format(b.index))
                idx = b.index
                self.blockchain.moveBlockToPool(idx) 
                
              Node.logger.info("forkstep2> add new blocks")
              Node.logger.info("fork7.blocks {} {}".format(type(blocks),blocks))
              blocks.reverse()
              for b in blocks:
                Node.logger.info("fork8.b {}".format(utils.obj2json(b)))
                if self.blockchain.addBlock(b):
                  self.txPoolRemove(b)
                  b.save()
                  b.removeFromPool()
                  self.updateUTXO(b)
              return True
            else:
              Node.logger.info("fork4.netx block")
              index = block.index - 1
              Node.logger.info("fork5.test {}".format(blocks,index))
              recursion=True
              break
      if i==len(fileset) - 1 and not recursion:
        Node.logger.info("fork9.find prev block in blockPool,but none can link fork block or can link main chain")
        break
    return False
    
  def tradeTest(self,nameFrom,nameTo,amount):
    if nameFrom=='me':
      wFrom = Wallete(self.me)
    else:
      wFrom = Wallete(nameFrom)
    if nameTo=='me':
      wTo = Wallete(self.me)
    else:
      wTo = Wallete(nameTo)
    return self.trade(
      wFrom.key[0],wFrom.key[1],wTo.key[1],amount)

  def trade(self,inPrvkey,inPubkey,outPubkey,amount):
    newTX=Transaction.newTransaction(
      inPrvkey,inPubkey,outPubkey,amount,self.tradeUTXO)
    newTXdict=None
    if newTX:
      newTXdict=utils.obj2dict(newTX)
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
      Node.logger.info("transaction广播完成")
    return newTXdict

  def genesisBlock(self,coinbase):
    newBlock=self.findNonce(Block(
      {"index":0,
      "prev_hash":"0",
      "data":[coinbase],
      "timestamp":time.time()}))
    newBlock.save()
    
  def mine(self,coinbase):
    Node.logger.info("is Mining...")
    #sync transaction from txPool
    txPool = self.txPoolSync()  
    txPoolDict=[]
    txPoolDict.append(coinbase)
    for item in txPool:
      txPoolDict.append(utils.obj2dict(item,sort_keys=True))
    currentChain = self.syncLocalChain() #gather last node
    prevBlock = currentChain.lastblock()
    
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
    index = newBlock.index
    nonce = newBlock.nonce
    filename = BROADCASTED_BLOCK_DIR + '%s_%s.json' % (index, nonce)
    with open(filename, 'w') as file:
      utils.obj2jsonFile(newBlock,file,sort_keys=True)
    #broadcast to peers
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
