from wallete import Wallete
from node import Node
from block import Block
from transaction import Transaction
from chain import UTXO
from flask import Flask,jsonify,request,render_template,make_response
    
import requests
import os
import json
import sys
import argparse
from config import *

import utils
import string,random,hashlib,time

#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--host",type=str,default="0.0.0.0",help="default ip is 0.0.0.0")
parser.add_argument("--port",type=int,default="5000",help="default port is 5000")
parser.add_argument("--name",type=str,help="name of wallete")

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
if args.name==None:
  args.name=me

#init
if not os.path.exists(PRIVATE_DIR):
  os.makedirs(PRIVATE_DIR)
if not os.path.exists(CHAINDATA_DIR):
  os.makedirs(CHAINDATA_DIR)
if not os.path.exists(UTXO_DIR):
  os.makedirs(UTXO_DIR)
if not os.path.exists(BROADCASTED_BLOCK_DIR):
  os.makedirs(BROADCASTED_BLOCK_DIR)
if not os.path.exists(BROADCASTED_TRANSACTION_DIR):
  os.makedirs(BROADCASTED_TRANSACTION_DIR)

#make pvkey,pbkey,wallete address  
myWallete=Wallete(args.name)
    
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
  t1=Transaction.newCoinbase(myWallete.address)
  coinbase=utils.obj2dict(t1)

  node.genesisBlock(coinbase)

#sync blockchain
node.syncOverallChain(save=True) 
#sync utxo
node.resetUTXO()

@app.route('/',methods=['GET'])
def default():
  return "hello youht"

@app.route('/index',methods=['GET'])
def react():
  return render_template('index.html',data="youht")

@app.route('/hash',methods=['GET'])
def testHash():

  result=[]
  t1=time.time()
  for i in range(50001):
    temp="".join(random.sample(string.ascii_letters,
                         random.randint(10,50)))
    hash=hashlib.sha256(temp.encode()).hexdigest()
    if i%10000==0:
     result.append({"hash":hash,"min":(time.time()-t1)/60,"count":i})
  t2=time.time()
  return  jsonify({"totalMin":(t2-t1)/60,"result":result})

#node function:list,register,unregister,sync
@app.route('/node/list',methods=['GET'])
def nodeList():
   utils.warning("node.nodes",node.nodes)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

@app.route('/node/sync',methods=['GET'])
def nodeSync():
  node.syncOverallNodes()
  response={
    'nodes': list(node.nodes)
  }
  return jsonify(response),200

@app.route('/node/register',methods=['GET'])
def nodeRegister():
   newNode=request.values.get("newNode")
   nodeSet = node.register(newNode)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

@app.route('/node/unregister',methods=['GET'])
def nodeUnregister():
   delNode=request.values.get("delNode")
   nodeSet = node.unregister(delNode)
   response={
      'nodes': list(node.nodes)
   }
   return jsonify(response),200

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

@app.route('/lastblock',methods=['GET'])
def lastblock():
  node.syncOverallChain(save=True)
  newBlock=node.blockchain.lastblock()
  return jsonify(utils.obj2dict(newBlock)),200

@app.route('/mine',methods=['GET'])
def mine():
  node.syncOverallChain(save=False) 

  t1=Transaction.newCoinbase(myWallete.address)
  coinbase=utils.obj2dict(t1)
  #mine
  newBlock=node.mine(coinbase)
  return jsonify(utils.obj2dict(newBlock)),200

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
      utils.obj2jsonFile(possible_block, block_file,sort_keys=True)
    return jsonify(confirmed=True)
  else:
    #ditch it
    return jsonify(confirmed=False)

@app.route('/transacted', methods=['POST'])
def transacted():
  possible_transaction_data = request.get_json()
  #validate possible_block
  possible_transaction = Transaction.parseTransaction(possible_transaction_data)
  if possible_transaction.isValid():
    #save to file to possible folder
    transaction_hash = possible_transaction.hash
    filename = BROADCASTED_TRANSACTION_DIR + '%s.json' % transaction_hash
    with open(filename, 'w') as transaction_file:
      utils.obj2jsonFile(possible_transaction,transaction_file,sort_keys=True)
    return jsonify(confirmed=True)
  else:
    #ditch it
    return jsonify(confirmed=False)

@app.route('/balance/<string:address>/',methods=['GET'])
def getBalance(address):
  value = node.utxo.getBalance(address)
  return jsonify({"address":address,"value":value})


@app.route('/blockchain', methods=['GET'])
def blockchainList():
  local_chain = node.syncLocalChain() 
  json_blocks = json.dumps(local_chain.block_list_dict())
  return json_blocks


@app.route('/block/<int:index>/',methods=['GET'])
def getBlock(index):
  block = node.blockchain.find_block_by_index(index)
  return jsonify(utils.obj2dict(block))
  
@app.route('/utxo/<string:address>/',methods=['GET'])
def findUTXO(address):
  utxo = node.utxo.findUTXO(address)
  return jsonify(utils.obj2dict(utxo))
  
@app.route('/transaction/<string:hash>/',methods=['GET'])
def findTransaction(hash):
  transaction = node.blockchain.findTransaction(hash)
  return jsonify(utils.obj2dict(transaction))

@app.route('/utxo/reset/',methods=['GET'])
def utxoReindex():
  utxoSet = node.resetUTXO()
  return jsonify(utils.obj2dict(utxoSet))


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
  app.run(host=node.host, port=node.port,debug=True,threaded=True)
