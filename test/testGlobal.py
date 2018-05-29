import builtins
def print_hello():
  print("hello")
ROOT = "hello"
builtins.__dict__["hello"]=print_hello