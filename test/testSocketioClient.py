import sys
sys.path.append('..')

from network import SocketioClient,BaseNamespace
import time

entry=["3b0_bc.youht.cc:8084","120.27.137.222:5000"]
class MyNamespace(BaseNamespace):
  def on_testResponse(self,data):
    print("response:",data)
  def on_connect(self):
    print("I connect")  
  def on_disconnect(self):
    print("I disconnect")
  def on_ping(self):
    print("ping...")
try:
  try:
    socketioClient=SocketioClient(entry[0],MyNamespace,'/pub',me="3b1_bc.youht.cc:8084")
    socketioClient.listenOnce("test","hello 3b0")
  except:
    socketioClient=SocketioClient(entry[1],MyNamespace,'/pub',me="3b1_bc.youht.cc:8084")
    socketioClient.listenOnce("test","hello 120")
    
except Exception as e:
  print("no entry",e)
#socketioClient.start()
  
