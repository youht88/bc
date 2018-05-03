class Leaf:
  def __init__(self,item):
    self.item = item
    self.left = None
    self.right = None

class Tree:
  def __init__(self):
    self.root = None

  def add(self, item):
    leaf = Leaf(item)
    if self.root is None:
      self.root = leaf
    else:
      q = [self.root]
      while True:
        pop_leaf = q.pop(0)
        if pop_leaf.left is None:
          pop_leaf.left = leaf
          return
        elif pop_leaf.right is None:
          pop_leaf.right = leaf
          return
        else:
          q.append(pop_leaf.left)
          q.append(pop_leaf.right)

  def traverse(self):  # 层次遍历
    if self.root is None:
      return None
    q = [self.root]
    res = [self.root.item]
    while q != []:
      pop_leaf = q.pop(0)
      if pop_leaf.left is not None:
        q.append(pop_leaf.left)
        res.append(pop_leaf.left.item)        
      if pop_leaf.right is not None:
        q.append(pop_leaf.right)
        res.append(pop_leaf.right.item)
    return res

  def preorder(self,root):  # 先序遍历
    if root is None:
      return []
    result = [root.item]
    left_item = self.preorder(root.left)
    right_item = self.preorder(root.right)
    return result + left_item + right_item
  
  def inorder(self,root):  # 中序序遍历
    if root is None:
      return []
    result = [root.item]
    left_item = self.inorder(root.left)
    right_item = self.inorder(root.right)
    return left_item + result + right_item
  
  def postorder(self,root):  # 后序遍历
    if root is None:
      return []
    result = [root.item]
    left_item = self.postorder(root.left)
    right_item = self.postorder(root.right)
    return left_item + right_item + result

t = Tree()
for i in range(10):
    t.add(i)
print('层序遍历:',t.traverse())
print('先序遍历:',t.preorder(t.root))
print('中序遍历:',t.inorder(t.root))
print('后序遍历:',t.postorder(t.root))