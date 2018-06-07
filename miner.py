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
import logger

import utils

import string,random,hashlib,time

import threading
import glob
import base64

from network import Gossip

import traceback


#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode","-e",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--host",type=str,default="0.0.0.0",help="default ip is 0.0.0.0")
parser.add_argument("--port",type=int,default="5000",help="default port is 5000")
parser.add_argument("--name",type=str,help="name of wallete")
parser.add_argument("--full",action="store_true",help="full sync")
parser.add_argument("--syncNode",action="store_true",help="if sync overall node")
parser.add_argument("--debug",action="store_true",help="if debug mode ")

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

#set logger
log = logger.Logger("miner","debug")
log.registHandler("./miner.log")
logger.logger = log

#make pvkey,pbkey,wallete address  
myWallete=Wallete(args.name)
    
log.error(args.me,args.port)
    
#make node
node=Node({"host":args.host,
           "port":args.port,
           "entryNode":args.entryNode,
           "me":args.me})
               
app = Flask(__name__)

#register me and get all alive ndoe list
if args.syncNode:
  node.syncOverallNodes()

log.debug(1,"debug")
log.info(2,"info")
log.warn(3,"warn")
log.error(4,"error")
log.critical(5,"critical")

log.info("1.node.nodes {}".format(node.nodes))
myGossip = Gossip(node.nodes,me)
log.info("2.node.nodes {}".format(node.nodes))

#genesis block ,only first node first time to use 
localChain = node.syncLocalChain()
if len(localChain.blocks)==0:
  #get zero block from entryNode
  res=node.httpProcess("http://"+node.entryNode+"/blockchain/0",3)
  try:
    result=res["response"].json()[0]
    genesisBlock=Block(result)
    if genesisBlock.isValid():
      genesisBlock.save()
    else:
      raise Exception("error on import genesisBlock")
  except:
    t1=Transaction.newCoinbase(myWallete.address)
    coinbase=utils.obj2dict(t1)
    node.genesisBlock(coinbase)


#sync blockchain
bestIndex = node.syncOverallChain(args.full) 

def blockerProcess():
  while True:
    if args.debug and len(threading.enumerate())!=4: #debug调试时使用
      continue
    if node.isMining or node.isBlockSyncing:
      time.sleep(2)
      continue
    node.isBlockSyncing=True
    try:
      maxindex = node.blockchain.maxindex()
      fileset=glob.glob(os.path.join(BROADCASTED_BLOCK_DIR, '%i_*.json'%(maxindex+1)))
      if len(fileset)>=1:        
        node.blockPoolSync()
      #print("blockPool={},threads={}".format(node.blockchain.maxindex(),len(threading.enumerate())))
    except Exception as e:
      log.critical(traceback.format_exc())
    node.isBlockSyncing=False
    time.sleep(2)
    
blocker=utils.CommonThread(blockerProcess,())
blocker.setDaemon(True)
blocker.start()

log.info("miner is ready")
#sync utxo
node.resetUTXO()

def minerProcess():
  while True:
    if node.isMining or node.isBlockSyncing:
      time.sleep(2)
      continue
    node.isMining=True
    try:
      txPoolFiles=glob.glob(
         os.path.join(BROADCASTED_TRANSACTION_DIR, '*.json'))
      if len(txPoolFiles)>=TRANSACTION_TO_BLOCK:
        log.info('the arg is:%s,%s\r' % (len(txPoolFiles),time.time()))
        t1=Transaction.newCoinbase(myWallete.address)
        coinbase=utils.obj2dict(t1)
        #mine
        newBlock=node.mine(coinbase)
      #print("txPool=",len(txPoolFiles))
    except Exception as e:
      log.critical(traceback.format_exc())
    node.isMining=False
    time.sleep(2)

miner = utils.CommonThread(minerProcess,())
miner.setDaemon(True)
miner.start()

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
    transaction_timestamp = possible_transaction.timestamp
    filename = BROADCASTED_TRANSACTION_DIR + '%s_%s.json' % (transaction_timestamp,transaction_hash)
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

@app.route('/blockchain/spv', methods=['GET'])
def blockchainListSPV():
  blockSPV = node.blockchain.getSPV()
  return jsonify(utils.obj2dict(blockSPV)),200

@app.route('/blockchain/<int:fromIndex>/<int:toIndex>', methods=['GET'])
def getRangeBlocks(fromIndex,toIndex):
  blocks = node.blockchain.findRangeBlocks(fromIndex,toIndex)
  return jsonify(utils.obj2dict(blocks)),200

@app.route('/blockchain/maxindex', methods=['GET'])
def getBlockchainMaxindex():
  return str(node.blockchain.maxindex()),200

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
  utxo = node.blockchain.utxo.findUTXO(address)
  return jsonify(utils.obj2dict(utxo))
  
@app.route('/transaction/<string:hash>/',methods=['GET'])
def findTransaction(hash):
  transaction = node.blockchain.findTransaction(hash)
  return jsonify(utils.obj2dict(transaction))

@app.route('/utxo/reset/',methods=['GET'])
def utxoReindex():
  utxoSet = node.resetUTXO()
  return jsonify(utils.obj2dict(utxoSet))

@app.route('/utxo/get/',methods=['GET'])
def utxoGet():
  utxoSet = node.blockchain.utxo
  utxoSummary = node.blockchain.utxo.getSummary()
  return jsonify({"summary":utxoSummary,"utxoSet":utils.obj2dict(utxoSet)})

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
  log.debug("hello youht")
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

@app.route('/wallete/me',methods=['GET'])
def getWallete():
  wallete = Wallete(me)
  balance = node.blockchain.utxo.getBalance(wallete.address)
  response = {"address":wallete.address,
              "pubkey":wallete.pubkey64D,
              "balance":balance}
  return jsonify(response)

@app.route('/wallete/<string:address>/',methods=['GET'])
def getBalance(address):
  if len(address)==64:
    balance = node.blockchain.utxo.getBalance(address)
    return jsonify({"address":address,"blance":balance})
  else:
    wallete = Wallete(address)
    balance = node.blockchain.utxo.getBalance(wallete.address)
    return jsonify({"address":wallete.address,"blance":balance})

@app.route('/wallete/create/<string:name>',methods=['GET'])
def createWallete(name):
  if name=='me':
    wallete = Wallete(me)
  else:
    wallete = Wallete(name)
  balance = node.blockchain.utxo.getBalance(wallete.address)
  response = {"address":wallete.address,
              "pubkey":wallete.pubkey64D,
              "balance":balance}
  return jsonify(response)

@app.route('/wallete/reset/<string:name>',methods=['GET'])
def syncWallete(name):
  result=node.httpProcess("http://"+name+"/wallete/me")
  dict=result["response"].json()
  address = dict["address"]
  pubkey64D = dict["pubkey"]
  try:
    os.mkdir("%s%s"%(PRIVATE_DIR,name))
  except:
    pass
  try:
    with open("%s%s/%s"%(PRIVATE_DIR,name,address),"w") as f:
      pass
    with open("%s%s/pubkey.pem"%(PRIVATE_DIR,name),"wb") as f:
      f.write(base64.b64decode(pubkey64D.encode()))
  except Exception as e:
    raise e
    return "error on wallete/reset/"+name
  return jsonify(dict)

@app.route('/trade/<nameFrom>/<nameTo>/<amount>',methods=['GET'])
def newTrade(nameFrom,nameTo,amount):
  response =node.tradeTest(nameFrom,nameTo,float(amount))
  if response:
    return jsonify(response)
  else:
    return "not have enouth money"

@app.route('/trade/utxo',methods=['GET'])
def getTradeUTXO():
  utxoSet = node.tradeUTXO.utxoSet
  utxoSummary = node.tradeUTXO.getSummary()
  return jsonify({"summary":utxoSummary,"utxoSet":utils.obj2dict(utxoSet)})
  
@app.route('/client/<key>/<value>',methods=['GET'])
def cli(key,value):
  t1=utils.CommonThread(myGossip.cli,(key,value))
  t1.start()
  t1.join()
  #myGossip.cli(key,value)
  return t1.getResult()

@app.route('/syn1/<key>/<valHash>/<node>',methods=['GET'])
def syn1(key,valHash,node):
  utils.CommonThread(myGossip.syn1,(key,valHash,node)).start()
  #myGossip.syn1(key,valHash,node)
  return "syn1 ok"

@app.route('/ack/<key>/<node>/',methods=['GET'])
def ack(key,node):
  utils.CommonThread(myGossip.ack,(key,node)).start()
  return "ack ok"
  
@app.route('/syn2/<key>/<value>/<node>',methods=['GET'])
def syn2(key,value,node):
  utils.CommonThread(myGossip.syn2,(key,value,node)).start()
  return "syn2 ok"
  
@app.route('/getValue/<key>',methods=['GET'])
def getValue(key):
  response = myGossip.getValue(key)
  return jsonify(response)

#start program
if __name__ == '__main__':
  app.run(host=node.host, port=node.port,debug=args.debug,threaded=True)
