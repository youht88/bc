import hashlib
import time
import string,random
import string,random

from multiprocessing import Process

def randomHash(n):
  for i in range(n):
    temp="".join(random.sample(string.ascii_letters,
                         random.randint(10,50)))
    hash=hashlib.sha256(temp.encode()).hexdigest()
  print(hash,(time.time()-s)/60,i)

s=time.time()
thread=[]
for i in range(8):
  thread.append(Process(target=randomHash,args=(1000000/8,)))
for i in thread:  
  i.start()
for i in thread:
  i.join()
print((time.time()-s)/60)