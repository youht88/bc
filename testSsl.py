from Crypto import Random
from Crypto.PublicKey import RSA

random_generate=Random.new().read
rsa = RSA.generate(1024,random_generate)

private_pem = rsa.exportKey()

print('\033[1;31;47mprivate_pem:\033[0m',private_pem)
with open('master-private.pem','wb') as f:
  f.write(private_pem)

public_pem=rsa.publickey().exportKey()

print('\033[1;31;47mpublic_pem:\033[0m',public_pem)
with open('master-public.pem','wb') as f:
  f.write(public_pem)

  
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.Hash import SHA
import base64

message = 'I love you'
with open('master-public.pem',"r") as f:
     key = f.read()
     rsakey = RSA.importKey(key)  # 导入读取到的公钥
     cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 生成对象
     cipher_text = base64.b64encode(cipher.encrypt(message.encode(encoding="utf-8")))  # 通过生成的对象加密message明文，注意，在python3中加密的数据必须是bytes类型的数据，不能是str类型的数据
     print("\033[1;31;47mencrypt:\033[0m",cipher_text)

with open('master-private.pem',"r") as f:
    key = f.read()
    rsakey = RSA.importKey(key)  # 导入读取到的私钥
    cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 生成对象
    text = cipher.decrypt(base64.b64decode(cipher_text), "ERROR")  # 将密文解密成明文，返回的是一个bytes类型数据，需要自己转换成str
    print("\033[1;31;47mdecrypt:\033[0m",text,"\n")

with open('master-private.pem',"r") as f:
    key = f.read()
    rsakey = RSA.importKey(key)
    signer = Signature_pkcs1_v1_5.new(rsakey)
    digest = SHA.new()
    digest.update(message.encode())
    sign = signer.sign(digest)
    signature = base64.b64encode(sign)
    print("\033[1;31;47msign:\033[0m",signature)

with open('master-public.pem',"r") as f:
  key = f.read()
  rsakey = RSA.importKey(key)
  verifier = Signature_pkcs1_v1_5.new(rsakey)
  digest = SHA.new()
  # Assumes the data is base64 encoded to begin with
  digest.update(message.encode())
  is_verify = verifier.verify(digest, base64.b64decode(signature))
  print("\033[1;31;47mverify:\033[0m",is_verify)
  
  