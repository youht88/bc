import hashlib
import math

class Leaf:
  def __init__(self):
    self.value = None
    self.left = None
    self.right = None

class Tree:
  def __init__(self,hashFun="sha256"):
    hashFun = hashFun.lower()
    if hashFun in ["sha256","sha1","sha512","md5"]:
      self.hashFun = getattr(hashlib,hashFun)
    else:
      self.hashFun = getattr(hashlib,"sha256")
    self.root = None
    self.levels=[]
  def addNode(self,left,right,data,hash=False):
    node = Leaf()
    if left==None and right==None:
      if hash:
        node.value = self.hashFun(data.encode()).hexdigest()
      else:
        node.value = data
    else: 
      if right.value==None:
        node.value = left.value
        node.left = left
      else:
        node.left = left
        node.right = right
        node.value = self.hashFun((left.value+right.value).encode()).hexdigest()
    return node          
  def makeTree(self,data,hash=False):
    nodes = []
    if len(data)%2 != 0:
      data.append(data[len(data) - 1])
    for item in data:
      node = self.addNode(None,None,item,hash)
      nodes.append(node)
    self.levels.append(nodes)
    for i in range(int(math.log2(len(data)))):
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
    
  def getProof(self, index):
    if self.levels is None:
      return None
    elif index > len(self.levels[0])-1 or index < 0:
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

  def validProof(self, proof, targetHash, merkleRoot):
    if len(proof) == 0:
      return targetHash == merkleRoot
    else:
      proofHash = targetHash
      for p in proof:
        try:
          # the sibling is a left node
          sibling = p['left']
          proofHash = self.hashFun((sibling + proofHash).encode()).hexdigest()
        except:
          # the sibling is a right node
          sibling = p['right']
          proofHash = self.hashFun((proofHash + sibling).encode()).hexdigest()
      return proofHash == merkleRoot
            
if __name__ == "__main__":
  t = Tree("md5")
  t.makeTree(["a","b","c","d"],True)
  print('*'*10,"merkleRoot",'*'*10)
  print("root:",t.root.value,"root.left:",t.root.left.value,"root.right:",t.root.right.value)
  print('*'*10,"merkleTree",'*'*10)
  for i in range(len(t.levels)):
    print("level{}:{}".format(i,[j.value for j in t.levels[i]]))
  for index in range(len(t.levels[0])):
    print('*'*10,"proof path of {}".format(index),'*'*10)
    proof = t.getProof(index)
    print([i for i in proof])
    print('*'*10,"validProof of {}".format(index),'*'*10)
    print(t.validProof(proof,t.levels[0][index].value,t.root.value))
  