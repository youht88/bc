from wallet import Wallet
from node import Node
from block import Block
from transaction import Transaction
from chain import UTXO
from flask import Flask,jsonify,request,render_template,make_response
from flask_socketio import SocketIO
from flask_socketio import send,emit
from flask_cors import CORS
    
import requests
import os,shutil
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
import copy


#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode","-e",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--host",type=str,default="0.0.0.0",help="default ip is 0.0.0.0")
parser.add_argument("--port",type=int,default="5000",help="default port is 5000")
parser.add_argument("--name",type=str,help="name of wallet")
parser.add_argument("--full",action="store_true",help="full sync")
parser.add_argument("--syncNode",action="store_true",help="if sync overall node")
parser.add_argument("--debug",action="store_true",help="if debug mode ")
parser.add_argument("--logging",type=str,choices=["debug","info","warn","error","critical"],default="debug",help="logging level:debug info warn error critical")
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

#clear transactionPool
try:
  shutil.rmtree("%s"%(BROADCASTED_TRANSACTION_DIR))
except:
  pass
if not os.path.exists(BROADCASTED_TRANSACTION_DIR):
  os.makedirs(BROADCASTED_TRANSACTION_DIR)

#set logger
log = logger.Logger("miner",args.logging)
log.registHandler("./miner.log")
logger.logger = log

#make pvkey,pbkey,wallet address  
mywallet=Wallet(args.name)
log.error(args.me,args.port)

#make node
node=Node({"host":args.host,
           "port":args.port,
           "entryNode":args.entryNode,
           "me":args.me})
               
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app,async_mode="threading")
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
    t1=Transaction.newCoinbase(mywallet.address)
    coinbase=utils.obj2dict(t1)
    node.genesisBlock(coinbase)


#sync blockchain
bestIndex = node.syncOverallChain(args.full) 

def blockerProcess():
  prevFileset=[]
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
      if len(fileset)>=1 and fileset!=prevFileset: #与上一次files集合不同
        prevFileset = fileset
        node.blockPoolSync()
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
    if args.debug and len(threading.enumerate())!=4: #debug调试时使用
      continue
    if node.isMining or node.isBlockSyncing:
      time.sleep(2)
      continue
    node.isMining=True
    try:
      txPoolFiles=glob.glob(
         os.path.join(BROADCASTED_TRANSACTION_DIR, '*.json'))
      if len(txPoolFiles)>=TRANSACTION_TO_BLOCK:
        log.info('the arg is:%s,%s\r' % (len(txPoolFiles),time.time()))
        t1=Transaction.newCoinbase(mywallet.address)
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
  log.info("recieve block index {}-{}".format(possible_block.index,possible_block.nonce))
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
  txDict = request.get_json()
  #validate possible_block
  TX = Transaction.parseTransaction(txDict)
  log.info("recieve transaction {}".format(TX.hash))
  if TX.isValid():
    utxoSet = copy.deepcopy(node.isolateUTXO.utxoSet)
    #log.critical("1",utxoSet)
    if node.isolateUTXO.updateWithTX(TX,utxoSet):
      node.isolateUTXO.utxoSet = utxoSet
      #save to file to transaction pool
      TXhash = TX.hash
      TXtimestamp = TX.timestamp
      filename = BROADCASTED_TRANSACTION_DIR + '%s_%s.json' % (TXtimestamp,TXhash)
      with open(filename, 'w') as f:
        utils.obj2jsonFile(TX,f,sort_keys=True)
      #handle isolatePool
      isolatePool = copy.copy(node.isolatePool) 
      for isolateTX in isolatePool:
        if node.isolateUTXO.updateWithTX(isolateTX,utxoSet):
          node.isolatePool.remove(isolateTX)
          #save to file to transaction pool
          TXhash = isolateTX.hash
          TXtimestamp = isolateTX.timestamp
          filename = BROADCASTED_TRANSACTION_DIR + '%s_%s.json' % (TXtimestamp,TXhash)
          with open(filename, 'w') as f:
            utils.obj2jsonFile(isolateTX,f,sort_keys=True)
        else:
          utxoSet = copy.deepcopy(node.isolateUTXO.utxoSet)
    else:
      node.isolatePool.append(TX)
    return jsonify(confirmed=True)
  else:
    #ditch it
    utils.warning("transaction is not valid,hash is:",TX.hash)
    return jsonify(confirmed=False)

@app.route('/getStatus',methods=['GET'])
def getStatus():
  status={
    "node.isMining":node.isMining,
    "node.isBlockSyncing":node.isBlockSyncing,
    "blockchain.maxindex":node.blockchain.maxindex(),
    "blockchain.maxindex.nonce":node.blockchain.blocks[node.blockchain.maxindex()].nonce    
  }
  return jsonify(status),200
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
@app.route('/blockchain/index/<int:blockIndex>/',methods=['GET'])
def getBlockByIndex(blockIndex):
  block = node.blockchain.findRangeBlocks(blockIndex,blockIndex)
  return jsonify(utils.obj2dict(block))

@app.route('/blockchain/hash/<string:blockHash>/',methods=['GET'])
def getBlockByHash(blockHash):
  block = node.blockchain.findBlockByHash(blockHash)
  return jsonify(utils.obj2dict(block))
  
@app.route('/blockchain/get/<string:peer>/<int:index>/',methods=['GET'])
def getRemoteBlocks(peer,index):
  result=node.httpProcess("http://"+peer+"/blockchain/index/"+str(index))
  blocksDict=result["response"].json()
  if blocksDict:
    block = Block(blocksDict[0])
    if block.isValid():
      #save to file to possible folder
      nonce = block.nonce
      filename = BROADCASTED_BLOCK_DIR + '%s_%s.json' % (index, nonce)
      with open(filename, 'w') as f:
        utils.obj2jsonFile(block,f,sort_keys=True)
    return jsonify(utils.obj2dict(block))
  else:
    return "no index {} from peer {}".format(index,peer) 
@app.route('/utxo/main/<string:address>/',methods=['GET'])
def findUTXO(address):
  utxo = node.blockchain.utxo.findUTXO(address)
  return jsonify(utils.obj2dict(utxo))

@app.route('/utxo/trade/<string:address>/',methods=['GET'])
def findTradeUTXO(address):
  utxo = node.tradeUTXO.findUTXO(address)
  return jsonify(utils.obj2dict(utxo))

@app.route('/utxo/isolate/<string:address>/',methods=['GET'])
def findIsolateUTXO(address):
  utxo = node.isolateUTXO.findUTXO(address)
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
  utxoSet = node.blockchain.utxo.utxoSet
  utxoSummary = node.blockchain.utxo.getSummary()
  return jsonify({"summary":utxoSummary,"utxoSet":utils.obj2dict(utxoSet,sort_keys=False)})

@app.route('/utxo/get/isolate',methods=['GET'])
def utxoGetIsolate():
  utxoSet = node.isolateUTXO.utxoSet
  utxoSummary = node.isolateUTXO.getSummary()
  return jsonify({"summary":utxoSummary,"utxoSet":utils.obj2dict(utxoSet,sort_keys=False)})

@app.route('/utxo/get/trade',methods=['GET'])
def utxoGetTrade():
  utxoSet = node.tradeUTXO.utxoSet
  utxoSummary = node.tradeUTXO.getSummary()
  return jsonify({"summary":utxoSummary,"utxoSet":utils.obj2dict(utxoSet,sort_keys=False)})

@app.route('/pool/transactions', methods=['GET'])
def getTxPool():
  txPool = node.txPoolSync() 
  data = json.dumps(txPool)
  return data
@app.route('/pool/isolate', methods=['GET'])
def getIsolatePool():
  return jsonify(utils.obj2dict(node.isolatePool,sort_keys=False))

@app.route('/lastblock',methods=['GET'])
def lastblock():
  newBlock=node.blockchain.lastblock()
  return jsonify(utils.obj2dict(newBlock)),200

@app.route('/mine',methods=['GET'])
def mine():
  t1=Transaction.newCoinbase(mywallet.address)
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
def index():
  return render_template('index.html',data="youht")

@app.route('/react',methods=['GET'])
def react():
  return render_template('react.html',data="youht")

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

@app.route('/wallet/me',methods=['GET'])
def getwallet():
  wallet = Wallet(me)
  balance = node.blockchain.utxo.getBalance(wallet.address)
  response = {"address":wallet.address,
              "pubkey":wallet.pubkey64D,
              "balance":balance}
  return jsonify(response)

@app.route('/wallet/<string:address>/',methods=['GET'])
def getBalance(address):
  if len(address)==64:
    balance = node.blockchain.utxo.getBalance(address)
    return jsonify({"address":address,"blance":balance})
  else:
    wallet = Wallet(address)
    balance = node.blockchain.utxo.getBalance(wallet.address)
    return jsonify({"address":wallet.address,"pubkey":wallet.pubkey64D,"blance":balance})

@app.route('/wallet/create/<string:name>',methods=['GET'])
def createwallet(name):
  if name=='me':
    wallet = Wallet(me)
  else:
    wallet = Wallet(name)
  balance = node.blockchain.utxo.getBalance(wallet.address)
  response = {"address":wallet.address,
              "pubkey":wallet.pubkey64D,
              "balance":balance}
  return jsonify(response)

@app.route('/wallet/get/<string:peer>/<name>',methods=['GET'])
def syncwallet(peer,name):
  result=node.httpProcess("http://"+peer+"/wallet/"+name)
  if name=='me':
    name=peer
  dict=result["response"].json()
  if "address" in dict:
    address = dict["address"]
    pubkey64D = dict["pubkey"]
    try:
      os.mkdir("%s%s"%(PRIVATE_DIR,name))
    except:
      shutil.rmtree("%s%s"%(PRIVATE_DIR,name))
      os.mkdir("%s%s"%(PRIVATE_DIR,name))
    try:
      with open("%s%s/%s"%(PRIVATE_DIR,name,address),"w") as f:
        pass
      with open("%s%s/pubkey.pem"%(PRIVATE_DIR,name),"wb") as f:
        f.write(base64.b64decode(pubkey64D.encode()))
    except Exception as e:
      raise e
      return "error on wallet/reset/"+name
  return jsonify(dict)

@app.route('/trade/<nameFrom>/<nameTo>/<amount>',methods=['GET'])
def newTrade(nameFrom,nameTo,amount):
  response =node.tradeTest(nameFrom,nameTo,float(amount))
  if response:
    return jsonify(response)
  else:
    return "not have enouth money"
  
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

@socketio.on('message')
def handle_message(message):
  print('received message:'+message)
  send("hello "+message)
  
@socketio.on('json')
def handle_json(json):
  print('received json:'+str(json))
  send({"a":1,"b":2},json=True)
  
@socketio.on('my event')
def handle_my_eustom_event(json):
  print('received my event json:'+str(json),type(json))
  emit('my response',{"x":"abc","y":999})
  for i in range(100):
    emit('idx',{"idx":i})
    emit('idx1',hashlib.sha256(str(i).encode()).hexdigest())
    time.sleep(0.5)  

#start program
if __name__ == '__main__':
  app.config['JSON_SORT_KEYS']=False
  socketio.run(app,host=node.host, port=node.port,debug=args.debug)
