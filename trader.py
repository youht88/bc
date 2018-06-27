from wallet import Wallet
from node import Node
from transaction import Transaction
import os
import json
import sys
import argparse
from config import *

import utils
import requests

import logger

#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--inAddr",type=str,help="which person to pay to")
parser.add_argument("--amount",type=float,help="how many to pay")
args=parser.parse_args()

#make and change work dir use args.me,otherwise use current dir
os.chdir(ROOT_DIR)
me=args.me
if me==None:
  try:
    with open(ME_FILE,"r") as f:
      me = f.read()
  except:
    raise Exception("if not define --me,you must define it in me file named by ME_FILE")
else:
  with open(ME_FILE,"w") as f:
    f.write(me)

try:
  os.chdir(me)
except:
  try:
    os.mkdir(me)
    os.chdir(me)
  except:
    pass

#set logger
log = logger.Logger("trader","info")
log.registHanddle("./trader.log")
logger.logger = log

#init
if not os.path.exists(PRIVATE_DIR):
  os.makedirs(PRIVATE_DIR)
if not os.path.exists(CHAINDATA_DIR):
  os.makedirs(CHAINDATA_DIR)
if not os.path.exists(BROADCASTED_BLOCK_DIR):
  os.makedirs(BROADCASTED_BLOCK_DIR)
if not os.path.exists(BROADCASTED_TRANSACTION_DIR):
  os.makedirs(BROADCASTED_TRANSACTION_DIR)

    
#make node
node=Node( {"entryNode":args.entryNode,
           "me":args.me})

#register me and get all alive ndoe list
node.syncOverallNodes()
#sync blockchain
node.syncOverallChain(save=True) 
temp = node.resetUTXO()

log.warning(utils.sha256(utils.obj2json(temp)))

#make pvkey,pbkey,wallet address  
youhtWallet=Wallet(me)
jinliWallet=Wallet("jinli")


coinbaseTX=Transaction.newCoinbase(youhtWallet.address)
print(utils.obj2json(coinbaseTX))

#UTXO=node.blockchain.findUTXO(youhtWallet.address)

value=node.utxo.getBalance(youhtWallet.address)
log.warning("{}'s wallet has {}".format(me,value))  
value1=node.utxo.getBalance(jinliWallet.address)
log.warning("jinli's wallet has {}".format(value1))  


node.tradeTest(me,'jinli',3)
node.tradeTest(me,'youyc',3)

#coinbase=utils.obj2dict(Transaction.newCoinbase(youhtWallet.address))
#mine
#node.mine(coinbase)
