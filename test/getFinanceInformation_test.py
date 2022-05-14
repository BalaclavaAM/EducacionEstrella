import json
from pprint import pprint
import unittest
import requests

class TestGetFinanceInformation(unittest.TestCase):
    CREDENTIALS = {"username":"Pepe","password":"Pepe123!"}
    
    def dummyLogin(self):
        self.assertTrue(True)
        body = requests.get("http://localhost:8080/login", data=json.dumps(self.CREDENTIALS), headers={"Content-Type":"application/json"})
        thejson = body.json()
        return (thejson['token']['access_token'], thejson['idUser'])
    
    def test_getFinanceInformationWAuth(self):
        token, usuario = self.dummyLogin()
        body = requests.get("http://localhost:8080/finance", headers={"Content-Type":"application/json", "authorization":token}, data=json.dumps({"idUser":usuario}))
        pprint(body.json())
        self.assertEqual(body.status_code, 200)
        
    def test_getFinanceInformationWOAuth(self):
        token, usuario = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InhFaV9ncjJWV1lzM09hckd1SGNuYSJ9.eyJpc3MiOiJodHRwczovL2Rldi11NnVrdDRsMS51cy5hdXRoMC5jb20vIiwic3ViIjoiaFc5aGJWMHVEUEVZQmFqOTd5d3lmajlpYVZSUkdjeGJAY2xpZW50cyIsImF1ZCI6IjE3Mi4yNC40MS4xNzA6ODA4MCIsImlhdCI6MTY1MjQ5OTI2OCwiZXhwIjoxNjUyNTg1NjY4LCJhenAiOiJoVzloYlYwdURQRVlCYWo5N3l3eWZqOWlhVlJSR2N4YiIsImd0eSI6ImNsaeSudC1jcmVkZW50aWFscyJ9.YR8lws2GBs3HYZHDksBQNWVwSw__Lhuw-5zkWs6l_I9howyKCcyts31NuZtGdVWPg7ffdu8bdoKUMX-DkzA2Cbv7UdAWIUjbM83cNHuKl7zx8PAXBafWa8T-DhY8LVQvGWuewpNaRcIskMe6ARtFne3xpA2YIjQYsqjVROy_0z36_GGksCnIVArsOqcWNYyMmYuwOGpHIzmr_kVX4EK_leorziI4KJR1OhFuGc5f3jyyRnWWb8hBJQ4F4j3HCdTAjKYLZASXIhNyw8rXU603j-BfPXtu3dL3u89Q-jnK1MnKoIMjf878SC1N3sdrO_z-iDAw3wsPirdQiX3fWmw79Q', 16
        body = requests.get("http://localhost:8080/finance", headers={"Content-Type":"application/json", "authorization":token}, data=json.dumps({"idUser":usuario}))
        pprint(body.json())
        self.assertEqual(body.status_code, 401)
        
        
    