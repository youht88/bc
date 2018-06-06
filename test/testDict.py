import sys
sys.path.append("../")
import utils
import logger 
class A(object):
  log=logger.logger
  def __init__(self):
    self.a=1
    self.b=2
  def update(self,c):
    self.c=3
    print(A.log)
  def __dicta__(self):
    return {"a":self.a,"c":self.c}
x=A()
x.update(3)
print(x)
print(x.__dicta__())
print(utils.obj2dict(x))
