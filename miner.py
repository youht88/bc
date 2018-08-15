from wallet import Wallet
from node import Node
from block import Block
from transaction import Transaction
from chain import UTXO
from flask import Flask,jsonify,request,render_template,make_response
from flask_socketio import SocketIO,send,emit
from flask_cors import CORS
from contract import Contract
    
import requests
import os,shutil
import json
import sys
import argparse
from config import *
import logger

import utils
import yaml

import string,random,hashlib,time

import threading
import glob
import base64

from network import Gossip

import traceback
import copy
import globalVar as _global

_global._init()

from kademlia import DHT

#args check & use help
parser=argparse.ArgumentParser()
parser.add_argument("--entryNode","-e",type=str,help="indicate which node to entry,e.g. ip|host:port ")
parser.add_argument("--me",type=str,help="indicate who am I,e.g. ip|host:port .Default to search 'me' file")
parser.add_argument("--httpServer",type=str,help="default httpServer is 0.0.0.0:5000")
parser.add_argument("--entryKad",type=str,help="entry node of kad,ip:port")
parser.add_argument("--db",type=str,help="db connect,ip:port/db")
parser.add_argument("--name",type=str,help="name of wallet")
parser.add_argument("--full",action="store_true",help="full sync")
parser.add_argument("--debug",action="store_true",help="if debug mode ")
parser.add_argument("--logging",type=str,choices=["debug","info","warn","error","critical"],default="debug",help="logging level:debug info warn error critical")

args=parser.parse_args()

#make and change work dir use args.me,otherwise use current dir
os.chdir(ROOT_DIR)

def syncConfigFile(args):
    with open(CONFIG_FILE,"r") as f:
      config=yaml.load(f.read())
      if not config:
        config={}
      else:
        config=config.get("blockchain")
        
      if args.me:
        config["me"]=args.me
      args.me = config.get("me")
      
      if args.entryNode:
        config["entryNode"]=args.entryNode
      args.entryNode = config.get("entryNode")
      
      if args.httpServer:
        config["httpServer"]=args.httpServer
      args.httpServer = config.get("httpServer")
      
      if args.entryKad:
        config["entryKad"]=args.entryKad
      args.entryKad = config.get("entryKad")
      
      if args.db:
        config["db"]=args.db
      args.db = config.get("db")
      
      if args.logging:
        config["logging"]=args.logging
      args.logging = config.get("logging")
      
      if args.name:
        config["name"]=args.name
      args.name = config.get("name")
      
      if args.full:
        config["full"]=args.full
      args.full = config.get("full")

      if args.debug:
        config["debug"]=args.debug
      args.debug = config.get("debug")
      
      if not (args.me and args.entryNode and args.entryKad and args.db and args.httpServer):
        raise Exception("you must define me,entryNode,entryKad,db,httpServer arguments")               
    with open(CONFIG_FILE,"w") as f:
      f.write(yaml.dump({"blockchain":config},default_flow_style=False))

#syncConfigFile
syncConfigFile(args)    
print(args)

try:
  os.chdir(args.me)
except:
  try:
    os.mkdir(args.me)
    os.chdir(args.me)
  except:
    pass
if args.name==None:
  args.name=args.me

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

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app,async_mode="threading")
#socketioTestClient= SocketIOTestClient(app,socketio,'/prv')
socketioTestClient=None

#make pvkey,pbkey,wallet address  
mywallet=Wallet(args.name)

#make node
node=Node({"httpServer":args.httpServer,
           "entryNode":args.entryNode,
           "entryKad":args.entryKad,
           "me":args.me,
           "db":args.db})
#gossip
#log.info("1.node.nodes {}".format(node.nodes))
#myGossip = Gossip(node.nodes,me)
#log.info("2.node.nodes {}".format(node.nodes))
               
#set socketio and socketio_client
node.setSocketio(socketio,socketioTestClient)

#time.sleep(1) #暂停1秒，因为setSocketio开启线程

#register me and get all alive ndoe list
node.syncOverallNodes()

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
log.critical("bestIndex:",bestIndex,"blockchain:",node.blockchain.maxindex())

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
      fileset=glob.glob(os.path.join(BROADCASTED_BLOCK_DIR, '*.json'))
      #fileset=list(filter(lambda x:int(x.split('_')[0])>maxindex,[os.path.basename(f) for f in fileset]))
      fileset=[os.path.basename(f) for f in fileset]
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

@app.route('/node/info',methods=['GET'])
def nodeInfo():
  peers=[]
  for i in list(node.nodes):
    peers.append({"peer":i,"isAlive":True})
  info={
    "peers":peers,
    "me":node.me,
    "entryNode":node.entryNode,
    "clientsNode":node.clientsNode,
    "wallet.address":mywallet.address,
    "wallet.balance":node.blockchain.utxo.getBalance(mywallet.address),
    "node.isMining":node.isMining,
    "node.isBlockSyncing":node.isBlockSyncing,
    "blockchain.maxindex":node.blockchain.maxindex(),
    "blockchain.maxindex.nonce":node.blockchain.blocks[node.blockchain.maxindex()].nonce    
  }
  return jsonify(info),200
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
  return 'ok',200

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
@app.route('/wallet/getAddress/<string:name>',methods=['GET'])
def getAddress(name):
  if name=='me':
    name=me
  wallet = Wallet(name)
  return wallet.address
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

@app.route('/wallet/get/peers',methods=['GET'])
def getPeersWallet():
  def printUrl(res,url,*args):
    log.critical(url)
  for peer in list(node.nodes):
    if not (peer == node.me):
      node.httpProcess("http://{}/wallet/get/{}/me".format(node.me,peer),timeout=3,
          cb=printUrl)
  return 'ok'
@app.route('/trade/<nameFrom>/<nameTo>/<amount>',methods=['POST'])
def newTrade1(nameFrom,nameTo,amount):
  script = request.form.get('script',default="")
  response =node.tradeTest(nameFrom,nameTo,float(amount),script)
  errCode = response.get("errCode")
  if not errCode:
    return jsonify(response)
  else:
    return response.get("errText")

@app.route('/trade/<nameFrom>/<nameTo>/<amount>',methods=['GET'])
def newTrade2(nameFrom,nameTo,amount):
  log.critical("trade get test")
  response =node.tradeTest(nameFrom,nameTo,float(amount))
  errCode = response.get("errCode")
  if not errCode:
    return jsonify(response)
  else:
    return response.get("errText")

#Gossip
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

#SocketIO

@socketio.on('connect',namespace='/pub')
def socketioConnect():
  sid = request.sid
  clientName = request.args.to_dict().get("me")
  if clientName==None or clientName in node.clientsNode:
    return False
  node.clientsNode[clientName]=sid
  emit('wellcome',clientName,broadcast=True,include_self=False)
  print("[client {}({}) connected ]".format(clientName,sid))

@socketio.on('disconnect',namespace='/pub')
def socketioDisconnect():
  sid = request.sid
  clientName = request.args.to_dict().get("me")
  node.clientsNode.pop(clientName)
  emit('goodbye',clientName,broadcast=True,include_self=False)
  print("[client {}({}) disconnect]".format(clientName,sid))

@socketio.on('getNodes',namespace='/pub')
def socketioGetNodes(data):
  print("*"*20,"getNodes","*"*20)
  peers=list(node.nodes)
  print(peers)
  emit('getNodesResponse',peers)

@socketio.on('getNodes',namespace='/prv')
def socketioGetNodesResponse(data):
  print("*"*20,"getNodes","*"*20)
  print(data)
  node.nodes=node.nodes.union(data)

@socketio.on('test','/')
def socketioTest0(data):
  print("recieve",data+'0')
  emit('testResponse',data.upper()+'0')
  return data[0].upper()+data[1:]+'0'

@socketio.on('test','/pub')
def socketioTest(data):
  print("recieve",data)
  emit('testResponse',data.upper())
  return data[0].upper()+data[1:]

@socketio.on('test','/pub1')
def socketioTest1(data):
  print("recieve1",data+'1')
  emit('testResponse',data.upper()+'1')
  return data[0].upper()+data[1:]+'1'
  
@socketio.on('entryServer',namespace='/pub')
def socketioEntryServerPub(data):
  print('3.geted from follower client',data)
  node.handleData(data)
    
  if node.me != data["source"]:  
    print("4.local client send to entry server!")
    if node.socketioClient and node.socketioClient.client:
      node.socketioClient.client.emit("entryServer",data,namespace='/pub')
    else:
      print("socketioClient is None or socketioClient.client is None")
    print('5.local server broadcast to follower client')
    emit("broadcast",data,include_self=False,broadcast=True,namespace='/pub')
  else:
    print(node.me,' == ',data["source"])

@socketio.on('localServer',namespace='/prv')
def socketioEntryServerPrv(data):
  print('9.geted from my local client',data)
  node.handleData(data)
    
  if node.me != data["source"]:  
    print('10.local server broadcast to follower client')
    emit("broadcast",data,include_self=False,broadcast=True,namespace='/pub')
    emit("localServerResponse","broadcasted!")
      
@app.route('/socket/<data>',methods=['GET'])
def testSocket(data):
  print("[test socket]")
  print(node.socketioClient)
  print(node.socketioClient.client)
  node.socketioClient.client.emit('test',data)
  return 'ok'

@socketio.on_error()        # Handles the default namespace
def error_handler(e):
    log.critical("on_error",e)

@socketio.on_error('/pub') # handles the '/chat' namespace
def error_handler_chat(e):
    log.critical("on_error/pub",e)

@socketio.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    log.critical("on_error_default",e)
      
#Kademlia
@app.route('/kad/set/<key>/<value>',methods=['GET'])
def kadSet(key,value):
  node.dht[key]=value
  return 'ok'

@app.route('/kad/get/<key>',methods=['GET'])
def kadGet(key):
  res = node.dht[key]
  return utils.obj2json(res)
    
@app.route('/kad/data',methods=['GET'])
def kadGetdata():
  return utils.obj2json(node.dht.data)
@app.route('/kad/buckets',methods=['GET'])
def kadGetbuckets():
  return utils.obj2json(node.dht.buckets.buckets)

#script
@app.route('/check/script',methods=['POST'])
def checkScript():
  script = request.form.get('script',default="")
  contract = Contract(script)
  result = contract.check()
  if result["errCode"]==0:
    return result["result"]
  else:
    return result["errText"]

#start program
if __name__ == '__main__':
  app.config['JSON_SORT_KEYS']=False
  host,port = args.httpServer.split(':')
  socketio.run(app,host=host, port=int(port),debug=args.debug)
