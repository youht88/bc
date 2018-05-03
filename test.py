#coding:utf-8

from transaction import Transaction
from block import Block
from chain import Chain
from wallete import Wallete

import os
import utils
import base64
import requests
import json
import os,sys

from config import *


key1=(pvkey,pbkey)=utils.genRSAKey("pvkey1.pem","pbkey1.pem")
key2=(pvkey,pbkey)=utils.genRSAKey("pvkey2.pem","pbkey2.pem")
key3=(pvkey,pbkey)=utils.genRSAKey("pvkey3.pem","pbkey3.pem")
'''
#encrypt & decrypt
message={"msg":"I love you!"}
#cipherText = utils.encrypt(message,key[1])
cipherText = utils.encrypt(message,None,"pbkey1.pem")
#print(cipherText)
#text = utils.encrypt(message,key[0])
text = utils.decrypt(cipherText,None,"pvkey1.pem")
print(text)


#sign & verify
message={"outPbKey":key1[1].decode(),"inPbKey":key2[1].decode(),"amount":200}
#sign=utils.sign(message,None,"pvkey.pem")
sign=utils.sign(message,key1[0])
#print(sign)
#is_verify=utils.verify(message,sign,None,"pbkey.pem")
is_verify=utils.verify(message,sign,key1[1])
print(is_verify)
'''
utils.debug("info","测试blockchain","hello")
utils.danger("测试交易验证","haha")

item1={"outPrvkey":key1[0],"outPubkey":key1[1],"inPubkey":key2[1],"amount":200}
transaction1=Transaction(item1)
item2={"outPrvkey":key2[0],"outPubkey":key2[1],"inPubkey":key1[1],"amount":100}
transaction2=Transaction(item2)
item3={"outPrvkey":key3[0],"outPubkey":key3[1],"inPubkey":key1[1],"amount":999}
transaction3=Transaction(item3)
transactions = [transaction1,
                transaction2,
                transaction3]
for i in transactions:
  print("transaction1 verify is ",utils.danger(i.isValid()),i.hash)
  
utils.success("测试block验证")
if not os.path.exists(CHAINDATA_DIR):
    #check if chaindata folder exists.
    os.mkdir(CHAINDATA_DIR)
if not os.path.exists(
    "%s000000.json"%CHAINDATA_DIR):
    block_zero_dir = {"index": "0", "timestamp": "1508895381", "prev_hash": "", "data": [],
        "diffcult":0}
    block_zero = Block(block_zero_dir)
    block_zero.self_save()
    print("block_zero is %s"% str(block_zero.is_valid()))
one_block = mine.mine_for_block([item2,item1])


utils.success("测试chain验证")
blockchain = sync.sync_local()
assert blockchain.is_valid()

utils.success("测试transaction广播")
item={"outPrvkey":key1[0],"outPubkey":key1[1],"inPubkey":key2[1],"amount":999}

new_transaction = Transaction(item)

transaction_dict = new_transaction.to_dict()
for peer in PEERS:
  try:
    res = requests.post("%stransacted"%peer,json=transaction_dict)
  except Exception as e:
    print("%s error is %s"%(peer,e))  
utils.warning("transaction广播完成")

utils.success("测试mine广播")

possible_transactions = sync.sync_possible_transactions()  
print('-'*20,'\n',possible_transactions)
possible_transactions_dict=[]
for item in possible_transactions:
  possible_transactions_dict.append(item.to_dict())
  os.remove(BROADCASTED_TRANSACTION_DIR+item.hash+".json")
new_block = mine.mine_for_block(possible_transactions_dict)

block_dict = new_block.to_dict()
for peer in PEERS:
  try:
    res = requests.post("%smined"%peer,json=block_dict)
  except Exception as e:
    print("%s error is %s"%(peer,e))  
utils.warning("mine广播完成")