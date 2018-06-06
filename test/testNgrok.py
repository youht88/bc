#coding:utf-8
#curl 3b1.intall.youht.cc:8081 | sh
import platform
from enum import Enum
import bash
import logging
import yaml
import argparse
import os
import logging

parser=argparse.ArgumentParser()
parser.add_argument("--bcDomain",type=str,required=True,help="indicate blockchain tunnel domain,e.g. zw.bc ")
parser.add_argument("--bcPort",type=str,required=True,help="indicate blockchain tunnel prot,e.g. 5000 ")
parser.add_argument("--ssh",type=str,required=True,help="indicate ssh remote_port ")
args=parser.parse_args()

##### set loggert #####
logger = logging.getLogger("ngrok") 
logger.setLevel(logging.DEBUG) #指定最低的日志级别

ch = logging.StreamHandler() #日志输出到屏幕控制台
ch.setLevel(logging.DEBUG) #设置日志等级

fh = logging.FileHandler('test.log')
fh.setLevel(logging.INFO) #设置输出到文件最低日志级别

formatter = logging.Formatter('%(asctime)s %(name)s- %(levelname)s - %(message)s') #定义日志输出格式
#add formatter to ch and fh
ch.setFormatter(formatter) #选择一个格式
fh.setFormatter(formatter)
 
logger.addHandler(ch) #增加指定的handler
logger.addHandler(fh)
# 'application' code


class System(Enum):
  Linux="Linux"
  Window="Window"
  Darwin="Darwin"

class Machine(Enum):
  x86_64="x86_64"
  armv7l="armv7l"
  armv6l="armv6l"
  s390x="s390x" 

logger.info("determin platform")
def getName():
  s=platform.system()
  m=platform.machine()
  logger.debug("{}-{}-{}-{}".format(s,m,System.Linux.value,Machine.armv6l.value))
  if s==System.Linux.value and m==Machine.x86_64.value:
    return "ngrok_linux64"
  elif s==System.Linux.value and m in [Machine.armv7l.value,Machine.armv6l.value]:
    return "ngrok_arm"
  elif s==System.Darwin.value and m==Machine.x86_64.value:
    return "ngrok_mac"
  elif s==System.Window.value and m==Machine.x86_64.value:
    return "ngrok_windows.exe"
  else:
    return ""

filename=getName()
logger.info("filename:{}".format(filename))

if platform.system() in [System.Linux.value,System.Darwin.value]:
  #config enviorment
  #bash.bash("pip3 install pymongo ")
  try:
    os.chdir("/usr/local/bin/")
  except:
    pass
      
  logger.debug("get ngrok bin")
  if not os.path.exists(filename):
    bash.bash("wget http://3b0.ftp.youht.cc:8081/{}".format(filename))
  bash.bash("chmod +x {}".format(filename))

  logger.debug("make ngrok.cfg")
  config = {
    "server_addr": "youht.cc:8083",
      "trust_host_root_certs": False, 
      "tunnels":
        {"blockchain":
          {"subdomain": args.bcDomain,
            "proto":
              {"http": args.bcPort}
          }
        },
      "ssh":
        {"remote_port": args.ssh,
         "proto":
          {"tcp": 22}
        }
    }
  with open("ngrok.cfg","w") as f:
    yaml.dump(config,f)
  
  logger.warn("add to boot service")
  hasNgrok=False
  with open("/etc/rc.local","r",encoding="utf-8") as f:
    lines = f.readlines() 
    #写的方式打开文件
    with open("/etc/rc.local","w",encoding="utf-8") as f_w:
      for line in lines:
        if "ngrok.cfg" in line:
          line = "nohup /usr/local/bin/{} --config /usr/local/bin/ngrok.cfg start-all &".format(filename)
          hasNgrok=True
          f_w.write(line)
        if not hasNgrok and "exit 0" in line:
          hasNgrok = True
          line = "nohup /usr/local/bin/{} --config /usr/local/bin/ngrok.cfg start-all &".format(filename)
          f_w.write(line)
          line = "exit 0"
          f_w.write(line)          
  logger.error("start server background")