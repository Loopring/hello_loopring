import json
import requests
from py_eth_sig_utils import utils as sig_utils
from py_eth_sig_utils.signing import v_r_s_to_signature
import time

from sdk.sig_utils.eddsa_utils import OriginTransferEddsaSignHelper
from sdk.sig_utils.ecdsa_utils import EIP712, generateTransferEIP712Hash
from sdk.loopring_v3_client import EthSignType

whitelisted = False # Set to False if you are the whitelisted professional user.
eth_private_key = "0x1" # EOA only

# use exported UAT account from beta.loopring.io
export_account = {
    "name" : "DEV Account 1",
    "exchangeName": "LoopringDEX: V2",
    "chainId": 5, # UAT in goerli, chainID is 5
    "exchangeAddress": "0x2e76EBd1c7c0C8e7c2B875b6d505a260C525d25e",
    "accountAddress": "",
    "accountId": 0,
    "apiKey": "",
    "publicKeyX": "0x0",
    "publicKeyY": "0x0",
    "privateKey": "0x0"
}

print("1. Query user balance")
response = requests.request(
  method="GET",
  url="https://uat2.loopring.io/api/v3/user/balances",
  headers={"X-API-KEY": export_account['apiKey']},
  params={
    "accountId": export_account['accountId'],
    "tokens": '0'
    }
)
print("user balance:")
print(json.dumps(response.json(), indent=4, sort_keys=False))

print("2. Query token storageId")
response = requests.request(
  method="GET",
  url="https://uat2.loopring.io/api/v3/storageId",
  headers={"X-API-KEY": export_account['apiKey']},
  params={
    "accountId": export_account['accountId'],
    "sellTokenId": 0
  }
)
print("token 0 storageId:")
print(json.dumps(response.json(), indent=4, sort_keys=False))
storageId = response.json()["offchainId"]

print("3. Query transfer fee")
response = requests.request(
  method="GET",
  url="https://uat2.loopring.io/api/v3/user/offchainFee",
  headers={"X-API-KEY":  export_account['apiKey']},
  params={
    "accountId": export_account['accountId'],
    "requestType": 3,
    "tokenSymbol": "ETH"
  }
)
print("token ETH transfer fee:")
print(json.dumps(response.json(), indent=4, sort_keys=False))
feeToken = 0 #response.json()["fees"][0]["token"]
feeAmount = response.json()["fees"][0]["fee"]

print("4. Request transfer")
transferReq = {
  "exchange": export_account["exchangeAddress"],
  "payerId": export_account["accountId"],
  "payerAddr":  export_account["accountAddress"],
  "payeeId": 0, # if you don't know the dest id, leave it to 0.
  "payeeAddr": "0xAA520c7F9674aAB15e6d3A98A72A93eAe6E751b0",
  "token": {
    "tokenId": 0,
    "volume": "1000000000000000000"
  },
  "maxFee" : {
    "tokenId": 0,
    "volume": feeAmount
  },
  "storageId": storageId,
  "validUntil": 1700000000,
  "memo": f"tutorial test {storageId}"
}

signer = OriginTransferEddsaSignHelper(export_account["privateKey"])
signedMessage = signer.sign(transferReq)
transferReq.update({"eddsaSignature": signedMessage})

headers={
    "X-API-KEY": export_account["apiKey"]
}
if not whitelisted:
    EIP712.init_env(name="Loopring Protocol",
                    version="3.6.0",
                    chainId=export_account['chainId'],
                    verifyingContract=export_account['exchangeAddress'])
    message = generateTransferEIP712Hash(transferReq)
    # print(f"transfer message hash = {bytes.hex(message)}")
    ethPrivKey = int(eth_private_key, 16).to_bytes(32, byteorder='big')
    v, r, s = sig_utils.ecsign(message, ethPrivKey)
    # will put into header, need L1 sig verification
    headers.update({'X-API-SIG': "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712})

response = requests.request(
  method="POST",
  url="https://uat2.loopring.io/api/v3/transfer",
  headers=headers,
  json=transferReq
)
print(json.dumps(response.json(), indent=4, sort_keys=False))

print("5. Query last transfer status")
response = requests.request(
  method="GET",
  url="https://uat2.loopring.io/api/v3/user/transfers",
  headers={"X-API-KEY": export_account["apiKey"]},
  params = {
    "accountId": export_account["accountId"],
    "start": int(time.time()*1000 - 3 * 1000),
    "tokenSymbol": "ETH"
  }
)
print(json.dumps(response.json(), indent=4, sort_keys=False))
