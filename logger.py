import logging
import logging.handlers  

import inspect

logger={}

class Logger(object):
  def __init__(self,name=None,level="NOTSET"):
    ##### set logger #####
    self.logger = logging.getLogger(name)
    self.logger.propagate=False #避免被第三方logging定义导致重复输出
    level = level.upper() 
    if level=="NOTSET":
      self.logger.setLevel(logging.NOTSET)
    elif level=="DEBUG":
      self.logger.setLevel(logging.DEBUG) #指定最低的日志级别
    elif level=="INFO":
      self.logger.setLevel(logging.INFO)
    elif level=="WARN":
      self.logger.setLevel(logging.WARN)
    elif level=="ERROR":
      self.logger.setLevel(logging.ERROR)
    elif level=="CRITICAL":
      self.logger.setLevel(logging.CRITICAL)
    else:
      self.logger.setLevel(logging.NOTSET)
      
    self.formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s') #定义日志输出格式
    
    channel = logging.StreamHandler() #日志输出到屏幕控制台
    channel.setFormatter(self.formatter)
    self.logger.addHandler(channel)
    
  def registHandler(self,filename,mode="w",maxBytes=2*1024*1024,backupCount=4):
    #channel = logging.FileHandler(filename,mode="w")
    channel = logging.handlers.RotatingFileHandler(filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount) 
    channel.setFormatter(self.formatter)
    self.logger.addHandler(channel)
  def getStack(self):
    filename = inspect.stack()[2][1]
    lineno = str(inspect.stack()[2][2])
    return "{}[{}]-".format(filename,lineno)
  def debug(self,*data):
    if len(data)==1:
      self.logger.debug(self.getStack()+"\033[1;35m"+str(data[0])+"\033[0m")
    else:
      self.logger.debug(self.getStack()+"\033[1;35m"+" ".join(str(i) for i in data)+"\033[0m")
  def info(self,*data):
    if len(data)==1:
      self.logger.info(self.getStack()+"\033[1;36m"+str(data[0])+"\033[0m")
    else:
      self.logger.info(self.getStack()+"\033[1;36m"+" ".join(str(i) for i in data)+"\033[0m")
  def warn(self,*data):
    if len(data)==1:
      self.logger.warn(self.getStack()+"\033[1;33m"+str(data[0])+"\033[0m")
    else:
      self.logger.warn(self.getStack()+"\033[1;33m"+" ".join(str(i) for i in data)+"\033[0m")
  def warning(self,*data):
    if len(data)==1:
      self.logger.warning(self.getStack()+"\033[1;33m"+str(data[0])+"\033[0m")
    else:
      self.logger.warning(self.getStack()+"\033[1;33m"+" ".join(str(i) for i in data)+"\033[0m")
  def error(self,*data):
    if len(data)==1:
      self.logger.error(self.getStack()+"\033[1;31m"+str(data[0])+"\033[0m")
    else:
      self.logger.error(self.getStack()+"\033[1;31m"+" ".join(str(i) for i in data)+"\033[0m")
  def critical(self,*data):
    print(self.logger.handlers)
    if len(data)==1:
      self.logger.critical(self.getStack()+"\033[1;37;41m"+str(data[0])+"\033[0m")
    else:
      self.logger.critical(self.getStack()+"\033[1;37;41m"+" ".join(str(i) for i in data)+"\033[0m")

