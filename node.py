import os
import json
import urllib.parse as urlparse
import requests
import datetime as date
import glob

from config import *
import utils

from chain import Chain,UTXO
from block import Block
from transaction import Transaction
from wallete import Wallete

import threading
import time
import random
import copy


class Node(object):
  def __init__(self,dict):
    self.me = dict["me"]
    self.entryNode=dict["entryNode"]
    if hasattr(self,'host'):
      self.host=dict["host"]
    else:
      self.host="0.0.0.0"
    if hasattr(self,'port'):
      self.port=dict["port"]
    else:
      self.port=5000
    
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
        print('*'*5,'\n',todoNodes,'\n','*'*5)
        try:
          print("-------------------")
          res = requests.get("http://"+node+"/node/register",params={"newNode":self.me},timeout=3)
          comeinNodes=set(res.json()["nodes"])
          doneNodes.add(node)
          todoNodes=(todoNodes | comeinNodes) - doneNodes
          print("comeinNodes",comeinNodes)
          print("doneNodes",doneNodes)
          print("todoNodes",todoNodes)
        except Exception as e:
          print("error on ",node," current done",self.nodes,repr(e))
      self.nodes =  doneNodes 
      self.save()
    
  def register(self,newNode):
    self.nodes.add(newNode)
    utils.warning("begin write",self.nodes)
    self.save()
    utils.warning("end write",self.nodes)
    return self.nodes
    
  def save(self):
    with open(self.peersFile,'w') as f:
      nodes=[item+'\n' for item in self.nodes]
      utils.warning(nodes)
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
            print(filepath+" error!")
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
      utils.danger("Peer at %s not running. Continuing to next peer." % peer)
    except requests.exceptions.ReadTimeout:
      utils.warning("Peer at %s timeout. Continuing to next peer." % peer)
    except Exception as e:
      utils.warning("Peer at %s error."% peer,e)
    else:
      utils.success("Peer at %s is running. " % peer)
    return result
    
  def peerHttp(self,path,timeout,cb,percent=1,nodes=[],*cbArgs):
    if nodes==[]:
      nodes = self.getRandom(percent)
    threads=[]
    event = threading.Event()
    print("path,timeout,cb,percent,nodes,cbArgs:",path,timeout,cb,percent,nodes,cbArgs)
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
         utils.warning("get {} blocks from {}".format(len(blocks),url))
         for block in blocks:
           if block.isValid():
             block.saveToPool()
      except:
         utils.warning("error on syncRangeChain")

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

    utils.warning("setp1:get highest nodes list")
    path = '/blockchain/maxindex'
    result = self.peerHttp(path,3,getHighestNodes,1,[],bestIndex)
    print("getHighestNodes1:",result) 
    for i,peer in enumerate(result): 
      if "bestIndex" in peer:
        if peer["bestIndex"]>bestIndex:
          bestIndex=peer["bestIndex"]
          nodes=[]
          nodes.append(peer["peer"])
        elif peer["bestIndex"] == bestIndex:
          nodes.append(peer["peer"])
    print("getHightestNodes2:",nodes)
    
    utils.warning("step2:put range block into blockPool from each node")
    fromIndex = localIndex + 1 
    if fromIndex<0:
      fromIndex = 0
    self.syncToBlockPool(nodes,fromIndex,bestIndex) 
    utils.warning("step3:wait blockPoolSync to build a bestChain")
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
    utxoset = self.blockchain.utxo.update(newblock)
    return utxoset
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
            print("error on:",filepath)
          txPool.append(
            Transaction.parseTransaction(txPoolDict))
    return txPool
  def txPoolRemove(self,block):
    #remove transactions in txPool
    if block:
      for TX in block.data:
        if TX.isCoinbase():
          continue
        txFile= os.path.join(BROADCASTED_TRANSACTION_DIR,TX.hash+".json")
        try:
          os.remove(txFile)
          utils.warning("del:",txFile)
        except:
          utils.warning("del file not found:",txFile)
          pass
  def blockPoolSync(self):
    maxindex = self.blockchain.maxindex()
    if os.path.exists(BROADCASTED_BLOCK_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(maxindex+1)))
      for filepath in fileset:
        with open(filepath, 'r') as blockFile:
          try:
            blockDict = json.load(blockFile)
            block = Block(blockDict)
            if block.isValid():
              print("0",self.blockchain.maxindex())
              if self.blockchain.addBlock(block):
                print("1","txPoolRemove",block.index)
                self.txPoolRemove(block)
                print("2","block.save")
                block.save()
                print("3","remove file",filepath)
                os.remove(filepath)
                print("4","befor update utxo",self.blockchain.maxindex())
                utxoSet = self.updateUTXO(block)
                #self.tradeUTXO = copy.deepcopy(utxoSet) 
                print("5","after update utxo",self.blockchain.utxo.getSummary())
              else:
                if self.resolveFork(block):
                  break
          except Exception as e:
            raise e
            print("error on:",filepath,e)
          finally:
            print("current blockchain high:",self.blockchain.maxindex())

  def resolveFork(self,forkBlock):
    blocks=[forkBlock]
    index = forkBlock.index - 1
    print("0.begin resolveFork",blocks[0].index,index)
    while True :
      fork=blocks[-1]
      fileset=glob.glob(
           os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(index)))
      i=-1
      print(fileset,blocks[-1].index)
      if len(fileset)==0:
        print("not find prev block in blockPool",index)
        break
      recursion=False
      for i,filepath in enumerate(fileset):
        with open(filepath,'r') as blockFile:
          block = Block(json.load(blockFile))
          print("1.test block.isValid")
          if block.isValid():
            print("2.test fork.prev_hash == block.hash")
            if fork.prev_hash != block.hash:
              continue
            print("3.test block.prev_hash can link blockchain",block.prev_hash,self.blockchain.findBlockByIndex(index - 1).hash)
            blocks.append(block) 
            if index==0 or block.prev_hash == self.blockchain.findBlockByIndex(index - 1).hash:
              #done,replace blocks in blockchain,move correspondent into blockPool
              utils.warning("step1> move correspondent into blockPool")
              index = block.index - 1
              
              for b in blocks[1:]:
                print("6.b.index",b.index)
                idx = b.index
                self.blockchain.moveBlockToPool(idx) 
                
              utils.warning("step2> add new blocks")
              print("7.blocks",type(blocks),blocks)
              blocks.reverse()
              for b in blocks:
                print("8.b",utils.obj2json(b))
                if self.blockchain.addBlock(b):
                  self.txPoolRemove(b)
                  b.save()
                  b.removeFromPool()
                  self.updateUTXO(b)
              return True
            else:
              print("4.netx block")
              index = block.index - 1
              print("5.test",blocks,index)
              recursion=True
              break
      if i==len(fileset) - 1 and not recursion:
        print("9.find prev block in blockPool,but none can link fork block or can link main chain")
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
            print("%s successed."%peer)
          else:
            print("%s error is %s"%(peer,res.status_code))
        except Exception as e:
          print("%s error is %s"%(peer,e))  
      utils.warning("transaction广播完成")
    return newTXdict

  def genesisBlock(self,coinbase):
    newBlock=self.findNonce(Block(
      {"index":0,
      "prev_hash":"0",
      "data":[coinbase],
      "timestamp":time.time()}))
    newBlock.save()
    
  def mine(self,coinbase):
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
    utils.warning("begin mine...",index)
    newBlock = self.findNonce(Block(blockDict))
    if newBlock==None:
      utils.warning("other miner mined")
      return "other miner mined"
    utils.warning("end mine.",index)
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
        print("%s error is %s"%(peer,e))  
      else:
        print("%s_%s success send to %s"%(index,nonce,peer))
    utils.warning("mine广播完成")
    
    #以下由blockPoolSync处理
    #newBlock.save()
    #self.blockchain.add_block(newBlock)
    #self.updateUTXO(newBlock)
    
    return newBlock
  
  def findNonce(self,newBlock):
    print("mining for block %s" % newBlock.index)
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
      
    print ("block %s mined. Nonce: %s , hash: %s" % (newBlock.index, newBlock.nonce,newBlock.hash))
    utils.success("block #"+
          str(newBlock.index)+
          " is",newBlock.isValid())
    return newBlock #we mined the block. We're going to want to save it
