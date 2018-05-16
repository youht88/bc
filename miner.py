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

import threading
import glob

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
      args.me=me
  except :
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

def minerProcess():
  while True:
    try:
      txPoolFiles=glob.glob(
         os.path.join(BROADCASTED_TRANSACTION_DIR, '*.json'))
      if len(txPoolFiles)>=TRANSACTION_TO_BLOCK:
        print ('the arg is:%s,%s\r' % (len(txPoolFiles),time.time()))
        t1=Transaction.newCoinbase(myWallete.address)
        coinbase=utils.obj2dict(t1)
        #mine
        newBlock=node.mine(coinbase)
      
      time.sleep(10)
      #print("txPool=",len(txPoolFiles))
    except Exception as e:
      print(e)
      #raise e

def blockerProcess():
  while True:
    #if self.event.wait(timeout=1):
    #  break
    if threading.enumerate()[-1].name=='Thread-1': #debug调试时使用
      try:
        maxindex = node.blockchain.maxindex()
        fileset=glob.glob(os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(maxindex+1)))
        if len(fileset)>=1:        
          node.blockPoolSync()
        print("blockPool=",node.blockchain.maxindex())
      except Exception as e:
        print(e)
        raise e
    time.sleep(10)
  
event = threading.Event()

miner = utils.CommonThread(name="MineThread",func=minerProcess,event=event,args=())
miner.setDaemon(True)
miner.start()

#blocker = BlockThread(event)
blocker=utils.CommonThread(name="BlockThread",func=blockerProcess,event=event,args=())
blocker.setDaemon(True)
blocker.start()


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


@app.route('/mined', methods=['POST'])
def mined():
  possible_block_data = request.get_json()
  #validate possible_block
  possible_block = Block(possible_block_data)
  if possible_block.isValid():
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
    utils.warning("transaction is not valid,hash is:",possible_transaction.hash)
    return jsonify(confirmed=False)

@app.route('/blockchain', methods=['GET'])
def blockchainList():
  blocks = node.blockchain.blocks
  return jsonify(utils.obj2dict(blocks)),200

@app.route('/blockchain/<int:fromIndex>/<int:toIndex>', methods=['GET'])
def getRangeBlocks(fromIndex,toIndex):
  blocks = node.blockchain.findRangeBlocks(fromIndex,toIndex)
  return jsonify(utils.obj2dict(blocks)),200

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found this url'}), 404)

#test url
@app.route('/blockchain/<int:index>/',methods=['GET'])
def getBlocks(index):
  blocks = node.blockchain.findRangeBlocks(index,index)
  return jsonify(utils.obj2dict(blocks))
  
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

@app.route('/balance/<string:address>/',methods=['GET'])
def getBalance(address):
  value = node.utxo.getBalance(address)
  return jsonify({"address":address,"value":value})

@app.route('/pool/transactions', methods=['GET'])
def getTxPool():
  txPool = node.txPoolSync() 
  data = json.dumps(txPool)
  return data

@app.route('/lastblock',methods=['GET'])
def lastblock():
  newBlock=node.blockchain.lastblock()
  return jsonify(utils.obj2dict(newBlock)),200

@app.route('/mine',methods=['GET'])
def mine():
  t1=Transaction.newCoinbase(myWallete.address)
  coinbase=utils.obj2dict(t1)
  #mine
  newBlock=node.mine(coinbase)
  return jsonify(utils.obj2dict(newBlock,indent=2)),200
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

@app.route('/wallete/<string:name>',methods=['GET'])
def getWallete(name):
  if name=='me':
    wallete = Wallete(me)
  else:
    wallete = Wallete(name)
  balance = node.utxo.getBalance(wallete.address)
  response = {"address":wallete.address,
              "pubkey":wallete.pubkey64D,
              "balance":balance}
  return jsonify(response)

@app.route('/trade/<nameFrom>/<nameTo>/<amount>',methods=['GET'])
def newTrade(nameFrom,nameTo,amount):
  response =node.tradeTest(nameFrom,nameTo,float(amount))
  return jsonify(response)

@app.route('/syncToPool/<int:fromIndex>/<int:toIndex>',methods=['GET'])
def syncToPool(fromIndex,toIndex):
  cnt = len(node.nodes) - 1
  step = (toIndex - fromIndex) // cnt
  path = []
  begin = fromIndex
  end = fromIndex + step 
  for i in range(cnt):
    path.append("blockchain/{}/{}".format(begin,end))
    begin = end +1
    if begin+step > toIndex:
      end = toIndex
    else:  
      end = begin+step
  response = node.randomPeerHttp(cnt,path,3,node.syncToPool)
  return jsonify(response)

#start program
if __name__ == '__main__':
  app.run(host=node.host, port=node.port,debug=True,threaded=True)
