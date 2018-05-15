import os
import json
from urllib.parse import urlparse
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
    local_chain = Chain([])
    #We're assuming that the folder and at least initial block exists
    if os.path.exists(CHAINDATA_DIR):
      fileset=glob.glob(
         os.path.join(CHAINDATA_DIR, '*.json'))
      fileset.sort()
      for filepath in fileset:
        with open(filepath, 'r') as block_file:
          try:
            block_info = json.load(block_file)
          except:
            print(filepath+" error!")
            return local_chain
          local_block = Block(block_info)
          local_chain.add_block(local_block)
    return local_chain

  def httpProcess(self,peer,url,timeout,fun):
    try:
      res = requests.get(url,timeout=timeout)
      try:
        fun(res,url)
      except Exception as e:
        utils.danger("error on execute ",fun.__name__,e)
    except requests.exceptions.ConnectionError:
      utils.danger("Peer at %s not running. Continuing to next peer." % peer)
    except requests.exceptions.ReadTimeout:
      utils.warning("Peer at %s timeout. Continuing to next peer." % peer)
    else:
      utils.success("Peer at %s is running. " % peer)
  
  def randomPeerHttp(self,cnt,path,timeout,fun,*args):
    nodes=list(self.nodes)
    utils.warning(nodes,self.me)
    try:
      nodes.remove(self.me)
    except:
      pass
    if len(nodes)>=cnt:
      cnt=cnt
    else:
      cnt=len(nodes)
    utils.warning(cnt,path,random.sample(nodes,cnt))
    threads=[]
    event = threading.Event()
    for i,peer in enumerate(random.sample(nodes,cnt)):
      if peer == self.me:
        continue
      if type(path)==str:
        url = "http://"+peer+"/"+path
      elif type(path)==list:
        plen=len(path)
        url = "http://"+peer+"/"+path[i%plen]
      else:
        url = "http://"+peer
      threads.append(utils.CommonThread(name="httpProcess"+str(i),func=self.httpProcess,event=event,args=(peer,url,timeout,fun)))
    for j in threads:
      j.setDaemon(True)
      j.start()     
    return 'ok'   
               
  def syncToPool(self,res,url):
    try:
       blocks=[Block(bdict) for bdict in res.json()]
       utils.warning("get {} blocks from {}".format(len(blocks),url))
       for block in blocks:
         if block.isValid():
           block.saveToPool()
    except:
       utils.warning("error on syncRangeChain")
  def syncOverallChain(self,save=False):
    best_chain = self.syncLocalChain()
    
    for peer in self.nodes:
      #try to connect to peer
      if peer == self.me:
        continue
      peer_blockchain_url = "http://"+peer + '/blockchain'
      try:
        r = requests.get(peer_blockchain_url,timeout=3)
        try:
          peer_blockchain_dict = r.json()
          utils.danger(len(peer_blockchain_dict))
          peer_blocks = [Block(bdict) for bdict in peer_blockchain_dict]
          peer_chain = Chain(peer_blocks)
          utils.danger(peer_chain.isValid())
          if peer_chain.isValid() and peer_chain > best_chain:
            best_chain = peer_chain
        except Exception as e:
          utils.danger("error syncOverallChain",e)
          pass
      except requests.exceptions.ConnectionError:
        utils.danger("Peer at %s not running. Continuing to next peer." % peer)
      except requests.exceptions.ReadTimeout:
        utils.warning("Peer at %s timeout. Continuing to next peer." % peer)
      else:
        utils.success("Peer at %s is running. Gathered their blochchain for analysis." % peer)
    utils.danger("Longest blockchain is %s blocks" % len(best_chain))
    #for now, save the new blockchain over whatever was there
    self.blockchain = best_chain
    if save:
      best_chain.save()
    self.resetUTXO()
    return best_chain
  
  def resetUTXO(self):
    self.utxo = UTXO()
    self.utxo.reset(self.blockchain)
    return self.utxo.utxoSet
  
  def updateUTXO(self,newblock):
    utxoset = self.utxo.update(newblock)
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
          utils.warning("del:",filepath)
          os.remove(filepath)  
          txPool.append(
            Transaction.parseTransaction(txPoolDict))
    return txPool

  def blockPoolSync(self):
    maxindex = self.blockchain.maxindex()
    blockPool = []
    if os.path.exists(BROADCASTED_BLOCK_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(maxindex+1)))
      if len(fileset)>=1:
        filepath = fileset[0]
        with open(filepath, 'r') as blockFile:
          try:
            blockDict = json.load(blockFile)
            block = Block(blockDict)
            if block.isValid():
              block.save()
              self.blockchain.add_block(block)
              self.updateUTXO(block)
          except Exception as e:
            print("error on:",filepath,e)
          finally:
            print("current blockchain high:",self.blockchain.maxindex())
            os.remove(filepath)
      elif len(fileset)>1:
        pass
        
        
  #index=(os.path.split(filepath[:filepath.find("_")]))[1]
          
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
      inPrvkey,inPubkey,outPubkey,amount,self.utxo)
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
    print("mine for block sync")
    currentChain = self.syncLocalChain() #gather last node
    print("mine for block sync done")
    prevBlock = currentChain.lastblock()
    
    #mine a block with a valid nonce
    index = int(prevBlock.index) + 1
    timestamp = date.datetime.now().strftime('%s')
    data = txPoolDict
    prev_hash = prevBlock.hash
    nonce = 0  
    blockDict = utils.args2dict(CONVERSIONS=BLOCK_VAR_CONVERSIONS,index=index, timestamp=timestamp, data=data, prev_hash=prev_hash, nonce=nonce)
    newBlock = self.findNonce(Block(blockDict))
  
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
    utils.warning("mine广播完成")
    
    #newBlock.save()
    #self.blockchain.add_block(newBlock)
    #self.updateUTXO(newBlock)
    
    return newBlock
  
  def findNonce(self,newBlock):
    print("mining for block %s" % newBlock.index)
    newBlock.update_self_hash()#calculate_hash(index, prev_hash, data, timestamp, nonce)
    newBlock.diffcult = NUM_ZEROS
    while str(newBlock.hash[0:NUM_ZEROS]) != '0' * NUM_ZEROS:
      newBlock.nonce += 1
      newBlock.update_self_hash()
  
    print ("block %s mined. Nonce: %s , hash: %s" % (newBlock.index, newBlock.nonce,newBlock.hash))
    utils.success("block #"+
          str(newBlock.index)+
          " is",newBlock.isValid())
    return newBlock #we mined the block. We're going to want to save it

