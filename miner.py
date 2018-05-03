from wallete import Wallete
from node import Node
from block import Block
from transaction import Transaction
from flask import Flask, jsonify, request , render_template
import requests
import os
import json
import sys
import argparse
from config import *

import utils

#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--host",type=str,default="0.0.0.0",help="default ip is 0.0.0.0")
parser.add_argument("--port",type=int,default="5000",help="default port is 5000")
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

#make pvkey,pbkey,wallete address  
rootWallete=Wallete("root")
myWallete=Wallete("youht")
pay={"outPrvkey":rootWallete.key[0],
       "outPubkey":rootWallete.key[1],
       "inPubkey":myWallete.key[1],
       "amount":NUM_ZEROS}
    
#make node
node=Node({"host":args.host,
           "port":args.port,
           "entryNode":args.entryNode,
           "me":args.me})
    
app = Flask(__name__)

#register me and get all alive ndoe list
node.syncOverallNodes()

#genesis block ,only first node first time to use 
localChain = node.syncLocalChain()
if len(localChain.blocks)==0:
  node.genesisBlock()

#sync blockchain
node.syncOverallChain(save=True) 
   
#mine
node.mine(pay)

@app.route('/',methods=['GET'])
def default():
  return "hello youht"

@app.route('/react',methods=['GET'])
def react():
  return render_template('react.html',data="youht")

@app.route('/hello',methods=['GET'])
def hello():
  a=1
  for i in range(1,18000):
     a*=i
  return  json.dumps({"index":a})

#node function:list,register,unregister,sync
@app.route('/nodes/list',methods=['GET'])
def nodeList():
   utils.warning("node.nodes",node.nodes)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

@app.route('/nodes/sync',methods=['GET'])
def nodeSync():
  node.syncOverallNodes()
  response={
    'nodes': list(node.nodes)
  }
  return jsonify(response),200

@app.route('/nodes/register',methods=['GET'])
def nodeRegister():
   newNode=request.values.get("newNode")
   nodeSet = node.register(newNode)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

@app.route('/nodes/unregister',methods=['GET'])
def nodeUnregister():
   delNode=request.values.get("delNode")
   nodeSet = node.unregister(delNode)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

@app.route('/blockchain', methods=['GET'])
def blockchainList():
  local_chain = node.syncLocalChain() 
  json_blocks = json.dumps(local_chain.block_list_dict())
  return json_blocks

@app.route('/sbc.json', methods=['GET'])
def blockchain_simple():
  local_chain = node.syncLocalChain() 
  json_blocks = json.dumps(local_chain.block_list_simple_dict())
  return json_blocks

@app.route('/possible/blocks', methods=['GET'])
def getPossibleBlocks():
  possibleBlocks = node.syncPossibleBlocks()
  blocks=[]
  for item in possibleBlocks:
    blocks.append(item.to_dict()) 
  data = json.dumps(blocks)
  return data

@app.route('/possible/transactions', methods=['GET'])
def getPossibleTransactions():
  possibleTransactions = node.syncPossibleTransactions() 
  data = json.dumps(possibleTransactions)
  return data

@app.route('/mine',methods=['GET'])
def mine():
   node.mine()
   return "ok",200
@app.route('/mined', methods=['POST'])
def mined():
  possible_block_data = request.get_json()
  print("/"*40,"\n",possible_block_data)
  #validate possible_block
  possible_block = Block(possible_block_data)
  if possible_block.is_valid():
    #save to file to possible folder
    index = possible_block.index
    nonce = possible_block.nonce
    filename = BROADCASTED_BLOCK_DIR + '%s_%s.json' % (index, nonce)
    with open(filename, 'w') as block_file:
      json.dump(possible_block.to_dict(), block_file,sort_keys=True)
    return jsonify(confirmed=True)
  else:
    #ditch it
    return jsonify(confirmed=False)

@app.route('/transacted', methods=['POST'])
def transacted():
  possible_transaction_data = request.get_json()
  print("*"*40,"\n",possible_transaction_data)
  #validate possible_block
  possible_transaction = Transaction(possible_transaction_data)
  if possible_transaction.isValid():
    #save to file to possible folder
    transaction_hash = possible_transaction.hash
    filename = BROADCASTED_TRANSACTION_DIR + '%s.json' % transaction_hash
    with open(filename, 'w') as transaction_file:
      json.dump(possible_transaction.to_dict(), transaction_file,sort_keys=True)
    return jsonify(confirmed=True)
  else:
    #ditch it
    return jsonify(confirmed=False)

if __name__ == '__main__':
  app.run(host=node.host, port=node.port,debug=True,threaded=True)
