import json
import random
import socket
import socketserver
import threading
import time
import heapq
import hashlib

k = 3
alpha = 3
id_bits = 128
iteration_sleep = 1

class DHTRequestHandler(socketserver.BaseRequestHandler):
  def handle(self):
    try:
      message = json.loads(self.request[0].strip().decode())
      message_type = message["message_type"]
      if message_type == "ping":
          self.handle_ping(message)
      elif message_type == "pong":
          self.handle_pong(message)
      elif message_type == "find_node":
          self.handle_find(message)
      elif message_type == "find_value":
          self.handle_find(message, find_value=True)
      elif message_type == "found_nodes":
          self.handle_found_nodes(message)
      elif message_type == "found_value":
          self.handle_found_value(message)
      elif message_type == "store":
          self.handle_store(message)
    except (KeyError,ValueError) as e:
      pass
    client_host, client_port = self.client_address
    peer_id = message["peer_id"]
    new_peer = Peer(client_host, client_port, peer_id)
    self.server.dht.buckets.insert(new_peer)

  def handle_ping(self, message):
    client_host, client_port = self.client_address
    id = message["peer_id"]
    peer = Peer(client_host, client_port, id)
    peer.pong(socket=self.server.socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)
      
  def handle_pong(self, message):
      pass
      
  def handle_find(self, message, find_value=False):
    key = message["id"]
    id = message["peer_id"]
    client_host, client_port = self.client_address
    peer = Peer(client_host, client_port, id)
    response_socket = self.request[1]
    if find_value and (key in self.server.dht.data):
      value = self.server.dht.data[key]
      peer.found_value(id, value, message["rpc_id"], socket=response_socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)
    else:
      nearest_nodes = self.server.dht.buckets.nearest_nodes(id)
      if not nearest_nodes:
        nearest_nodes.append(self.server.dht.peer)
      nearest_nodes = [nearest_peer.astriple() for nearest_peer in nearest_nodes]
      peer.found_nodes(id, nearest_nodes, message["rpc_id"], socket=response_socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)

  def handle_found_nodes(self, message):
    rpc_id = message["rpc_id"]
    shortlist = self.server.dht.rpc_ids[rpc_id]
    del self.server.dht.rpc_ids[rpc_id]
    nearest_nodes = [Peer(*peer) for peer in message["nearest_nodes"]]
    shortlist.update(nearest_nodes)
      
  def handle_found_value(self, message):
    rpc_id = message["rpc_id"]
    shortlist = self.server.dht.rpc_ids[rpc_id]
    del self.server.dht.rpc_ids[rpc_id]
    shortlist.set_complete(message["value"])
      
  def handle_store(self, message):
    key = message["id"]
    self.server.dht.data[key] = message["value"]


class DHTServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
  def __init__(self, host_address, handler_cls):
    socketserver.UDPServer.__init__(self, host_address, handler_cls)
    self.send_lock = threading.Lock()

class DHT(object):
  def __init__(self, host, port, id=None, boot_host=None, boot_port=None):
    if not id:
      id = random_id()
    self.peer = Peer(str(host), port, id)
    self.data = {}
    self.buckets = BucketSet(k, id_bits, self.peer.id)
    self.rpc_ids = {} # should probably have a lock for this
    self.server = DHTServer(self.peer.address(), DHTRequestHandler)
    self.server.dht = self
    self.server_thread = threading.Thread(target=self.server.serve_forever)
    self.server_thread.daemon = True
    self.server_thread.start()
    self.bootstrap(str(boot_host), boot_port)
  
  def iterative_find_nodes(self, key, boot_peer=None):
    shortlist = Shortlist(k, key)
    shortlist.update(self.buckets.nearest_nodes(key, limit=alpha))
    if boot_peer:
      rpc_id = random.getrandbits(id_bits)
      self.rpc_ids[rpc_id] = shortlist
      boot_peer.find_node(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id)
    while (not shortlist.complete()) or boot_peer:
      nearest_nodes = shortlist.get_next_iteration(alpha)
      for peer in nearest_nodes:
        shortlist.mark(peer)
        rpc_id = random.getrandbits(id_bits)
        self.rpc_ids[rpc_id] = shortlist
        peer.find_node(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id) ######
      time.sleep(iteration_sleep)
      boot_peer = None
    return shortlist.results()
      
  def iterative_find_value(self, key):
    shortlist = Shortlist(k, key)
    shortlist.update(self.buckets.nearest_nodes(key, limit=alpha))
    while not shortlist.complete():
      nearest_nodes = shortlist.get_next_iteration(alpha)
      for peer in nearest_nodes:
        shortlist.mark(peer)
        rpc_id = random.getrandbits(id_bits)
        self.rpc_ids[rpc_id] = shortlist
        peer.find_value(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id) #####
      time.sleep(iteration_sleep)
    return shortlist.completion_result()
          
  def bootstrap(self, boot_host, boot_port):
    if boot_host and boot_port:
      boot_peer = Peer(boot_host, boot_port, 0)
      self.iterative_find_nodes(self.peer.id, boot_peer=boot_peer)
                  
  def __getitem__(self, key):
    hashed_key = hash_function(key)
    if hashed_key in self.data:
      return self.data[hashed_key]
    result = self.iterative_find_value(hashed_key)
    if result:
      return result
    else:
      return None
    #raise KeyError
      
  def __setitem__(self, key, value):
    hashed_key = hash_function(key)
    nearest_nodes = self.iterative_find_nodes(hashed_key)
    if not nearest_nodes:
        self.data[hashed_key] = value
    for node in nearest_nodes:
        node.store(hashed_key, value, socket=self.server.socket, peer_id=self.peer.id)
      
  def tick():
    pass

#################################

def largest_differing_bit(value1, value2):
  distance = value1 ^ value2
  length = -1
  while (distance):
      distance >>= 1
      length += 1
  return max(0, length)

class BucketSet(object):
  def __init__(self, bucket_size, buckets, id):
    self.id = id
    self.bucket_size = bucket_size
    self.buckets = [list() for _ in range(buckets)]
    self.lock = threading.Lock()
      
  def insert(self, peer):
    if peer.id != self.id:
      bucket_number = largest_differing_bit(self.id, peer.id)
      peer_triple = peer.astriple()
      with self.lock:
        bucket = self.buckets[bucket_number]
        if peer_triple in bucket: 
          bucket.pop(bucket.index(peer_triple))
        elif len(bucket) >= self.bucket_size:
          bucket.pop(0)
        bucket.append(peer_triple)
              
  def nearest_nodes(self, key, limit=None):
      num_results = limit if limit else self.bucket_size
      with self.lock:
        def keyfunction(peer):
          return key ^ peer[2] # ideally there would be a better way with names? Instead of storing triples it would be nice to have a dict
        peers = (peer for bucket in self.buckets for peer in bucket)
        best_peers = heapq.nsmallest(self.bucket_size, peers, keyfunction)
        return [Peer(*peer) for peer in best_peers]

##############################
class Peer(object):
  ''' DHT Peer Information'''
  def __init__(self, host, port, id):
    self.host, self.port, self.id = host, port, id
      
  def astriple(self):
    return (self.host, self.port, self.id)
      
  def address(self):
    return (self.host, self.port)
      
  def __repr__(self):
    return repr(self.astriple())

  def _sendmessage(self, message, sock=None, peer_id=None, lock=None):
    message["peer_id"] = peer_id # more like sender_id
    encoded = json.dumps(message).encode()
    if sock:
      if lock:
        with lock:
          sock.sendto(encoded, (self.host, self.port))
      else:
        sock.sendto(encoded, (self.host, self.port))
      
  def ping(self, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "ping"
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def pong(self, socket=None, peer_id=None, lock=None):
    message = {
       "message_type": "pong"
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def store(self, key, value, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "store",
        "id": key,
        "value": value
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def find_node(self, id, rpc_id, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "find_node",
        "id": id,
        "rpc_id": rpc_id
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def found_nodes(self, id, nearest_nodes, rpc_id, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "found_nodes",
        "id": id,
        "nearest_nodes": nearest_nodes,
        "rpc_id": rpc_id
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def find_value(self, id, rpc_id, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "find_value",
        "id": id,
        "rpc_id": rpc_id
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
      
  def found_value(self, id, value, rpc_id, socket=None, peer_id=None, lock=None):
    message = {
        "message_type": "found_value",
        "id": id,
        "value": value,
        "rpc_id": rpc_id
    }
    self._sendmessage(message, socket, peer_id=peer_id, lock=lock)
        
############################
def hash_function(data):
  return int(hashlib.md5(data.encode()).hexdigest(), 16)
    
def random_id(seed=None):
  if seed:
      random.seed(seed)
  return random.randint(0, (2 ** id_bits)-1)
    
##############################
class Shortlist(object):
  def __init__(self, k, key):
    self.k = k
    self.key = key
    self.list = list()
    self.lock = threading.Lock()
    self.completion_value = None
      
  def set_complete(self, value):
    with self.lock:
        self.completion_value = value
          
  def completion_result(self):
    with self.lock:
        return self.completion_value
      
  def update(self, nodes):
    for node in nodes:
        self._update_one(node)
      
  def _update_one(self, node):
    if node.id == self.key or self.completion_value:
      return
    with self.lock:
      for i in range(len(self.list)):
        if node.id == self.list[i][0][2]:
          break
        if node.id ^ self.key < self.list[i][0][2] ^ self.key:
          self.list.insert(i, (node.astriple(), False))
          self.list = self.list[:self.k]
          break
      else:
        if len(self.list) < self.k:
          self.list.append((node.astriple(), False))
                  
  def mark(self, node):
    with self.lock:
      for i in range(len(self.list)):
        if node.id == self.list[i][0][2]:
          self.list[i] = (node.astriple(), True)
                  
  def complete(self):
    if self.completion_value:
      return True
    with self.lock:
      for node, completed in self.list:
        if not completed:
          return False
      return True
          
  def get_next_iteration(self, alpha):
    if self.completion_value:
      return []
    next_iteration = []
    with self.lock:
      for node, completed in self.list:
        if not completed:
          next_iteration.append(Peer(*node))
          if len(next_iteration) >= alpha:
            break
    return next_iteration
      
  def results(self):
    with self.lock:
      return [Peer(*node) for (node, completed) in self.list]
      
if __name__=="__main__":
  host1, port1 = 'localhost', 3001
  dht1 = DHT(host1, port1,boot_host=host1,boot_port=3000)
  host2, port2 = 'localhost', 3002
  dht2 = DHT(host2, port2, boot_host=host1, boot_port=3000)
  host3,port3 = 'localhost',3003
  dht3 = DHT(host3, port3, boot_host=host2, boot_port=3000)
  host4,port4 = 'localhost',3004
  dht4 = DHT(host4, port4, boot_host=host4, boot_port=3000)
  #dht1["my_key"] = ["My", "json-serializable", "Object"]
  print("set key to dht2")
  dht2["my_key"]={"x":1,"y":{"a":2,"b":3}}
  
  print("get from dht1:",dht1["my_key"])
  print("get from dht3:",dht3["my_key"])
  print('*'*20,"dht1",'*'*20)
  print(dht1.data,dht1.buckets.buckets)
  print('*'*20,"dht2",'*'*20)
  print(dht2.data,dht2.buckets.buckets)
  print('*'*20,"dht3",'*'*20)
  print(dht3.data,dht3.buckets.buckets)
