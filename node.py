import os
import json
from urllib.parse import urlparse
import requests
import datetime as date
import glob

from config import *
import utils

from chain import Chain
from block import Block
from transaction import Transaction

import threading
import time

from utils import is_valid_chain


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
          res = requests.get("http://"+node+"/nodes/register",params={"newNode":self.me},timeout=3)
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
          peer_blocks = [Block(bdict) for bdict in peer_blockchain_dict]
          peer_chain = Chain(peer_blocks)
  
          if peer_chain.is_valid() and peer_chain > best_chain:
            best_chain = peer_chain
        except:
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
      best_chain.self_save()
    return best_chain
  
  def syncPossibleTransactions(self):
    possible_transactions=[]
    #We're assuming that the folder and at least initial block exists
    if os.path.exists(BROADCASTED_TRANSACTION_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_TRANSACTION_DIR, '*.json'))
      fileset.sort()
      for filepath in fileset:
        with open(filepath, 'r') as transaction_file:
          try:
            transaction_info = json.load(transaction_file)
          except:
            print(filepath)
            return possible_transactions
          possible_transactions.append( Transaction(transaction_info))
    return possible_transactions

  def syncPossibleBlocks(self):
    possible_blocks = []
    if os.path.exists(BROADCASTED_BLOCK_DIR):
      fileset=glob.glob(
         os.path.join(BROADCASTED_BLOCK_DIR, '*.json'))
      fileset.sort()
      print("????",self.blockchain.blocks)
      index = self.blockchain.maxindex()
      for filepath in fileset:
        fileIndex=(os.path.split(filepath[:filepath.find("_")]))[1]
        if int(fileIndex)<=index:
          utils.warning("del:",filepath)
          os.remove(filepath)
          continue
        with open(filepath, 'r') as block_file:
          try:
            block_info = json.load(block_file)
          except:
            print(filepath)
            return possible_blocks
          possible_blocks.append(Block(block_info))
    return possible_blocks

  def genesisBlock(self):
    newBlock=Block({"index":0,"prev_hash":"0","timestamp":time.time()})
    newBlock.self_save()
  def mine(self,pay):
    possibleTransactions = self.syncPossibleTransactions()  
    print('-'*20,'\n',possibleTransactions)
    possibleTransactionsDict=[]
    for item in possibleTransactions:
      possibleTransactionsDict.append(item.to_dict())
    
    possibleTransactionsDict.append(pay)
    print("possibleTransaction:",possibleTransactionsDict)

    new_block = self.mine_for_block(possibleTransactionsDict)
    
    block_dict = new_block.to_dict()
    for peer in self.nodes:
      if peer == self.me:
        continue
      try:
        res = requests.post("http://%s/mined"%peer,
                            json=block_dict,timeout=10)
      except Exception as e:
        print("%s error is %s"%(peer,e))  
    utils.warning("mine广播完成")
  
  def mine_for_block(self,transactions):
    print("mine for block sync")
    current_chain = self.syncLocalChain() #gather last node
    print("mine for block sync done")
    print("possible_block sync")
    possible_blocks=self.syncPossibleBlocks()
    print("abcd","\n",possible_blocks)
    print("possible_block sync done")
    prev_block = current_chain.lastblock()
    new_block = self.mine_blocks(prev_block,transactions)
    new_block.self_save()
    return new_block

  def mine_blocks(self,last_block,transactions):
    index = int(last_block.index) + 1
    timestamp = date.datetime.now().strftime('%s')
    
    #暂时关闭交易
    #data = transactions
    
    prev_hash = last_block.hash
    nonce = 0
  
    block_info_dict = utils.dictConvert1(CONVERSIONS=BLOCK_VAR_CONVERSIONS,index=index, timestamp=timestamp, data=data, prev_hash=prev_hash, nonce=nonce)
    new_block = Block(block_info_dict)
    return self.find_valid_nonce(new_block)
  
  def find_valid_nonce(self,new_block):
    print("mining for block %s" % new_block.index)
    new_block.update_self_hash()#calculate_hash(index, prev_hash, data, timestamp, nonce)
    new_block.diffcult = NUM_ZEROS
    while str(new_block.hash[0:NUM_ZEROS]) != '0' * NUM_ZEROS:
      new_block.nonce += 1
      new_block.update_self_hash()
  
    print ("block %s mined. Nonce: %s , hash: %s" % (new_block.index, new_block.nonce,new_block.hash))
  
    utils.success("block #"+
          str(new_block.index)+
          " is"),new_block.is_valid()
    return new_block #we mined the block. We're going to want to save it

