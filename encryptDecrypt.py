import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

def encryptString(stringToEncrypt:str)->str:
    public_key = RSA.import_key(open("public.pem").read())
    stringToEncrypt = str.encode(stringToEncrypt)
    
    rsa_public_key = PKCS1_OAEP.new(public_key)
    encrypted_text = rsa_public_key.encrypt(stringToEncrypt)
    encrypted_text = base64.b64encode(encrypted_text)
    return encrypted_text.decode('utf-8')

def decryptString(stringToDecrypt:str)->str:
    private_key = RSA.import_key(open("private.pem").read())
    rsa_private_key = PKCS1_OAEP.new(private_key)
    decrypted_text = rsa_private_key.decrypt(base64.b64decode(stringToDecrypt))
    
    return decrypted_text.decode('utf-8')