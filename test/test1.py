class Test1(object):
  def __init__(self,list0=[],set0=set(),
          dict0={},tuple0=()):
    self.list0 = list0
    self.set0 = set0
    self.dict0 = dict0
    self.tuple0= tuple0
    self.list1 = list(list0)
    self.set1 = set(set0)
    self.dict1 = dict(dict0)
    self.tuple1 = tuple(tuple0)
    print("list0,set0,dict0,tuple0:",list0,set0,dict0,tuple0)
    print("self list0,set0,dict0,tuple0:",self.list0,self.set0,self.dict0,self.tuple0)
    print("self list1,set1,dict1,tuple1:",self.list1,self.set1,self.dict1,self.tuple1)
    print("*"*5)
  def shallow(self,n):
    print("shallow copy test")
    a=self.list0
    b=self.set0
    c=self.dict0
    d=self.tuple0
    print("1.self.list0,a:",self.list0,a)
    print("1.self.set0,b:",self.set0,b)
    print("1.self.dict0,c:",self.dict0,c)
    print("1.self.tuple0,d:",self.tuple0,d)
    a.append(n)
    b.add(n)
    c["name"]=n
    #d[0]=n
    print("2.self.list0,a:",self.list0,a)
    print("2.self.set0,b:",self.set0,b)
    print("2.self.dict0,c:",self.dict0,c)
    print("2.self.tuple0,d:",self.tuple0,d)
  def deep(self,n):
    a=list(self.list1)
    b=set(self.set1)
    c=dict(self.dict1)
    d=tuple(self.tuple1)
    print("1.self.list1,a:",self.list1,a)
    print("1.self.set,b:",self.set1,b)
    print("1.self.dict,c:",self.dict1,c)
    print("1.self.set,d:",self.tuple1,d)
    a.append(n)
    b.add(n)
    c["name"]=n
    #d[0]=n
    print("2.self.list1,a:",self.list1,a)
    print("2.self.set1,b:",self.set1,b)
    print("2.self.dict1,a:",self.dict1,c)
    print("2.self.tuple1,b:",self.tuple1,d)
        
print('-'*10,"no argument",'-'*10)
x=Test1()
x.shallow(1)
print('*'*5)
x.deep(2)


print('-'*10,"have argument",'-'*10)
list0=[1,2,3]
set0={"a","b","c"}
dict0={"name":"youht"}
tuple0=("x","y","z")
y=Test1(list0,set0,dict0,tuple0)
y.shallow(1)
print('*'*5)
y.deep(2)
print("list",list0)
print("set",set0)
print("dict",dict0)
print("tuple",tuple0)