import time,pytz,datetime
import requests
import globalVar as _global

class Contract(object):
  def __init__(self,script,sandbox={}):
    self.status=0
    self.compileError=None
    self.executeError=None
    self.script=script
    self.setSandbox()
  def check(self):
    try:
      bin=compile(self.script,'','exec')
    except Exception as e:
      return {"errCode":2,"errText":repr(e)}
    try:
      exec(bin,{},self.sandbox)
      result=self.sandbox["main"](self.sandbox)
    except Exception as e:
      return {"errCode":3,"errText":repr(e)}
    return {"errCode":0,"result":"True" if result else "False"}
  def setSandbox(self):
    sandbox={}
    sandbox["blockchain"]=_global.get("blockchain")
    sandbox["node"] = _global.get("node")
    sandbox["dt"]=self.dt()
    sandbox["http"]=self.http
    self.sandbox=sandbox
  def dt(self):
    tz=pytz.timezone('Asia/Shanghai')
    dt=datetime.datetime.now(tz).strftime('%Y%m%d%H%M%S')
    return dt
  def http(self,url,params={},timeout=3):
    res = requests.get(url,params=params,timeout=timeout)
    return res