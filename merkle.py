import hashlib
import math
import utils

class Leaf(object):
  def __init__(self):
    self.value = None
    self.left = None
    self.right = None

class Tree(object):
  def __init__(self,hashFun="sha256"):
    hashFun = hashFun.lower()
    if hashFun in ["sha256","sha1","sha512","md5"]:
      self.hashFun = hashFun #getattr(hashlib,hashFun)
    else:
      self.hashFun = hashFun #getattr(hashlib,"sha256")
    self.root = None
    self.levels=[]
  def addNode(self,left,right,data,hash=False):
    hashFun = getattr(hashlib,self.hashFun)
    node = Leaf()
    if left==None and right==None:
      if hash:
        node.value = hashFun(data.encode()).hexdigest()
      else:
        node.value = data
    else: 
      if right.value==None:
        node.value = left.value
        node.left = left
      else:
        node.left = left
        node.right = right
        node.value = hashFun((left.value+right.value).encode()).hexdigest()
    return node          
  def makeTree(self,data,hash=False):
    nodes = []
    if len(data)%2 != 0:
      data.append(data[len(data) - 1])
    for item in data:
      node = self.addNode(None,None,item,hash)
      nodes.append(node)
    self.levels.append(nodes)
    for i in range(int(math.log2(len(data)))+1):
      newLevel = []
      for j in range(0,len(nodes),2):
        if j+1==len(nodes): 
          node = self.addNode(nodes[j],Leaf(),None)
        else:
          node = self.addNode(nodes[j],nodes[j+1],None)
        newLevel.append(node)
      nodes = newLevel
      self.levels.append(nodes)
    self.root = nodes[0]
    return self.root
    
  def getProof(self, index_targetHash):
    if type(index_targetHash)=="str":
      index = self.getIndex(index_targetHash)
    else:
      index = index_targetHash
    if self.levels is None:
      return None
    elif index==None or index > len(self.levels[0])-1 or index < 0:
      return None
    else:
      proof = []
      for x in range(len(self.levels)):
          level_len = len(self.levels[x])
          if (index == level_len - 1) and (level_len % 2 == 1):  # skip if this is an odd end node
              index = int(index / 2.)
              continue
          isRight = index % 2
          siblingIndex = index - 1 if isRight else index + 1
          siblingPos = "left" if isRight else "right"
          siblingValue = self.levels[x][siblingIndex].value
          proof.append({siblingPos: siblingValue})
          index = int(index / 2.)
      return proof
  def getIndex(self,hash):
    try:
      return list(map(lambda x:x.value,self.levels[0])).index(hash)
    except:
      return None 
  def validProof(self, proof, targetHash, merkleRoot):
    hashFun = getattr(hashlib,self.hashFun)
    if proof==None or len(proof) == 0:
      return targetHash == merkleRoot
    else:
      proofHash = targetHash
      for p in proof:
        try:
          # the sibling is a left node
          sibling = p['left']
          proofHash = hashFun((sibling + proofHash).encode()).hexdigest()
        except:
          # the sibling is a right node
          sibling = p['right']
          proofHash = hashFun((proofHash + sibling).encode()).hexdigest()
      return proofHash == merkleRoot
            
if __name__ == "__main__":
  t = Tree("md5")
  hashFun = getattr(hashlib,t.hashFun)
  t.makeTree([str(i) for i in range(1000)],True)
  '''
  print('*'*10,"merkleRoot",'*'*10)
  print(t.root.value,t.root.left.value)
  #print("root:",t.root.value,
  #      "root.left:",t.root.left.value,
  #      "root.right:",t.root.right.value)
  print('*'*10,"merkleTree",'*'*10)
  for i in range(len(t.levels)):
    print("level{}:{}".format(i,[j.value for j in t.levels[i]]))
  for index in range(len(t.levels[0])):
    print('*'*10,"proof path of index {}".format(index),'*'*10)
    proof = t.getProof(index)
    print([i for i in proof])
    print('*'*10,"validProof of index{}".format(index),'*'*10)
    print(t.validProof(proof,t.levels[0][index].value,t.root.value))
  '''
  search='123'
  value=hashFun(search.encode()).hexdigest()  
  index = t.getIndex(value)
  proof = t.getProof(index)
  print('*'*10,"validProof of {}".format(search),'*'*10)
  print("hash:{} \n index:{} \n proof path:{} \ntotal levels:{}".format(value,index,proof,len(t.levels)))
  print(len(t.levels[-1]),len(t.levels[-2]))
  print(t.validProof(proof,value,t.root.value))