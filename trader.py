from wallete import Wallete
from node import Node
from transaction import Transaction,TXin
import os
import json
import sys
import argparse
from config import *

import utils
import requests

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

#make pvkey,pbkey,wallete address  
youhtWallete=Wallete("youht")
jinliWallete=Wallete("jinli")

newTX=Transaction.newTransaction("jinli","youht",2,node.blockchain)

newTXdict=utils.obj2dict(newTX)

for peer in node.nodes:
  if peer==node.me:
    continue
  try:
    res = requests.post("http://%s/transacted"%peer,
                        json=newTXdict,timeout=10)
    print("%s successed."%peer)
  except Exception as e:
    print("%s error is %s"%(peer,e))  
utils.warning("transaction广播完成")

value=youhtWallete.getBalance(node.blockchain)
print("youht's wallete has {}".format(value))  