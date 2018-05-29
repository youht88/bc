class Publisher:
  def __init__(self):
    self.observer=[]
  def register(self,o):
    if o not in self.observer:
      self.observer.append(o)
  def unregister(self,o):
    try:
      self.observer.remove(o)
    except:
      pass
  def notify(self):
    [o.notify(self) for o in self.observer]
    
class Formater(Publisher):
  def __init__(self):
    Publisher.__init__(self)
    self._a = "None"
  def __str__(self):
    return "formater.__str__"+self.a
  @property
  def a(self):
    return self._a
  @a.setter
  def a(self,a):
    self._a = a
    self.notify()

class FormatA():
  def notify(self,publisher):
    print("hello {}".format(publisher.a))
class FormatB():
  def notify(self,publisher):
    print("{} ,你好".format(publisher.a))

f=Formater()
ca=FormatA()
cb=FormatB()
f.register(ca)
f.register(cb)
f.a="youht"
print(f)