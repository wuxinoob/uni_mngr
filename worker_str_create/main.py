import base64
from cryptography.fernet import Fernet
key = b'FMa8ZBISFRcOM_gZN2uatCf8-nW-d0SGghW__T4zRdw='
def hard_encrypt(text:str,key =None)->str:
  if not key:
      key = Fernet.generate_key()
  cipher_text = Fernet(key).encrypt(text.encode())
  return base64.b64encode(cipher_text).decode()

def tf_flie_gost():
    with open("worker_str_create/gost_info",mode="r",encoding=("utf-8"))as fd:
        a = fd.read()
    print(hard_encrypt(a,key))
def tf_flie_yaml():
    with open("worker_str_create/flying.yaml",mode="r",encoding=("utf-8"))as fd:
        a = fd.read()
    print(hard_encrypt(a,key))
tf_flie_yaml()