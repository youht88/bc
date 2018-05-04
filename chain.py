from block import Block
import utils

class Chain(object):
  '''
  def __init__(self, blocks=[]):
    self.blocks = blocks
  '''
  def __init__(self, blocks):
    self.blocks = blocks

  def is_valid(self):
    for index, cur_block in enumerate(self.blocks[1:]):
      prev_block = self.blocks[index]
      if prev_block.index+1 != cur_block.index:
        return False
      if not cur_block.is_valid(): #checks the hash
        return False
      utils.debug("warning",
        "verify prev block hash is this block prev_hash")
      if prev_block.hash != cur_block.prev_hash:
        return False
    return True

  def self_save(self):
    '''
      We want to save this in the file system as we do.
    '''
    for b in self.blocks:
      b.self_save()
    return True

  def find_block_by_index(self, index):
    if len(self) <= index:
      return self.blocks[index]
    else:
      return False

  def find_block_by_hash(self, hash):
    for b in self.blocks:
      if b.hash == hash:
        return b
    return False
  def findUTXO(self):
    pass
  def findUnspendTransactions(self,address):
    pass
  def findSpendableOutputs(self,address,amount):
    rtn = (acc,validOutputs)=(2,"abc")
    return rtn
  def __len__(self):
    return len(self.blocks)

  def __eq__(self, other):
    if len(self) != len(other):
      return False
    for self_block, other_block in zip(self.blocks, other.blocks):
      if self_block != other_block:
        return False
    return True

  def __ne__(self, other):
    return not self.__eq__(other)

  def __gt__(self, other):
    return len(self.blocks) > len(other.blocks)

  def __lt__(self, other):
    return len(self.blocks) < len(other.blocks)

  def __ge__(self, other):
    return self.__eq__(other) or self.__gt__(other)

  def __le__(self, other):
    return self.__eq__(other) or self.__lt__(other)

  def lastblock(self):
    return self.blocks[-1]
  def maxindex(self):
    '''
      We're assuming a valid chain. Might change later
    '''
    return self.blocks[-1].index

  def add_block(self, new_block):
    '''
      Put the new block into the index that the block is asking.
      That is, if the index is of one that currently exists, the new block
      would take it's place. Then we want to see if that block is valid.ls
      If it isn't, then we ditch the new block and return False.
    '''
    '''
      When we add a block, we want to find the block with the same index,
      remove the current block and the rest of the blocks with higher index,
      and
    '''
    if new_block.index > len(self):
      pass
    self.blocks.append(new_block)

    return True

  def block_list_dict(self):
    return [utils.obj2dict(b) for b in self.blocks]
    