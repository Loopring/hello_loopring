# Transfer Tutorial

## Getting started

In this tutorial we will demonstrate how to:

1. Connect to the loopring DEX.
2. Query assets in loopring DEX.
3. Make transfers.
4. Query transfer records.

## Export the loopring DEX Account

1. Export account info from Loopring DEX, take an account in [Loopring UAT env](beta.loopring.io) as an example. Also user may need eth private key to sign extra authentication to show the ownership of the L1 address. Professional users can register to a whitelist in Loopring to skip that check.

   ```python
   export_account = {
      "chainId": 5, # UAT in goerli, chainID is 5. ETH mainnet is 1.
   		"exchangeName": "Loopring Exchange v2",
      "exchangeAddress": "0x2e76EBd1c7c0C8e7c2B875b6d505a260C525d25e",
      "accountAddress": "0x2cA82103BF777bF0e7a73B9577Ce26CfFD9bec6f",
      "accountId": 10000,
      "apiKey": "JPxqxPF992s7KzN7SLSzhyccb3BAUY3HOtQnDylXWMiASnJADr4awM2MV2bWQGR0",
      "publicKeyX": "0x029ee1d99d7ee60047698db065f4845dbba642fcfd95a72ad267d467f4d37d54",
      "publicKeyY": "0xb777dcadaee66fadd6cef8c60107df88ace06bc5ab7ce3fb69206cf5d8b006a1",
      "privateKey": "0x4f7cb9a17e1d375947db4a0117a556047d81732cdb4b6ef0bff167c20bb1ee9"
   }
   
   eth_private_key = "0x0" # EOA private key to sign L1 authentication.
   whitelisted = False
   ```

## Query assets in loopring DEX

1. Make query request

```python
param = {
  "accountId": export_account['accountId'],
  "tokens": '0,1,2'
}
```

2. Get query response

```python
import requests

response = requests.request(
  method="GET",
  url="https://uat2.loopring.io/api/v3/user/balances",
  headers={"X-API-KEY": export_account['apiKey']},
  params=param
)
```

​	The response should be like:

```python
[
    {
        "tokenId": 0,
        "total": "1000000000000000000",
        "locked": "0",
        "pending": {
            "deposit": "0",
            "withdraw": "0"
        }
    },
    {
        "tokenId": 1,
        "total": "200000000000000000000",
        "locked": "0",
        "pending": {
            "deposit": "0",
            "withdraw": "0"
        }
    }
]
```

## Make transfers

1. Make a transfer request

   Before make transfer, user needs to get storageId of the token to be transferred, which is just like the nonce in ETH tx.

   ```python
   import requests
   
   response = requests.request(
     method="GET",
     url="https://uat2.loopring.io/api/v3/storageId",
     headers={"X-API-KEY": export_account['apiKey']},
     params={
       "accountId": export_account['accountId'],
       "sellTokenId": 0
     }
   )
   ```

   Response is:

   ```python
   {
       "offchainId": 1001,
       "orderId": 0
   }
   ```

   Then, user needs to query transfer fee requirement

   ```python
   import requests
   
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
   ```

   Response is like:

   ```python
   {
       "fees": [
           {
               "discount": 1,
               "fee": "26200000000000",
               "token": "ETH"
           },
           {
               "discount": 0.8,
               "fee": "165800000000000000",
               "token": "LRC"
           },
           {
               "discount": 0.8,
               "fee": "51800",
               "token": "USDT"
           },
           {
               "discount": 1,
               "fee": "647000000000000000",
               "token": "DAI"
           }
       ],
       "gasPrice": "30000000000"
   }
   ```

   Time to create transfer requirement:

   ```python
   transferReq = {
     "exchange": export_account["exchangeAddress"],
     "payerId": export_account["accountId"],
     "payerAddr":  export_account["accountAddress"],
     "payeeId": 0, # if you don't know the dest id, leave it to 0.
     "payeeAddr": "0xAA520c7F9674aAB15e6d3A98A72A93eAe6E751b0", # trans to a specific L2 account
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
   ```

2. Sign transfer request

   ```python
   from sdk.sig_utils.eddsa_utils import OriginTransferEddsaSignHelper
   
   signer = OriginTransferEddsaSignHelper(export_account["privateKey"])
   signedMessage = signer.sign(transferReq)
   transferReq.update({{"eddsaSignature": signedMessage}})
   ```

   Common users need extra L1 ecdsa authentication in request header to show their ownership of the address, so an extra signature based on L1 EIP712 is required. But this is not necessary for those professional users registerred to Loopring.

   ```python
   headers={
       "X-API-KEY": export_account["apiKey"]
   }
   if ecdsaAuth:
     message = generateTransferEIP712Hash(transferReq)
     # print(f"transfer message hash = {bytes.hex(message)}")
     v, r, s = sig_utils.ecsign(message, ecdsaKey)
     # will put into header, need L1 sig verification
     headers.update({'X-API-SIG': "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712})
   ```

3. Send to Loopring and wait for response

   ```python
   import requests
   
   response = requests.request(
     method="POST",
     url="https://uat2.loopring.io/api/v3/transfer",
     headers=headers,
     json=transferReq
   ```

   Then the response should be:

   ```python
   {
     'hash': '0x2a38b31988359f742c65b668853adaf82bade728f1faf8f0748283f853e83b59',
     'status': 'processing',
     'isIdempotent': False
   }
   ```

4. Check transfer record

   ```python
   response = requests.request(
     method="GET",
     url="https://uat2.loopring.io/api/v3/user/transfers",
     headers={"X-API-KEY": export_account["apiKey"]},
     params = {
       "accountId": export_account["accountId"]
     }
   )
   ```

   The records is as below:

   ```python
   {
     "totalNum": 2,
     "transactions": [
       {
         "amount": "100000000000000000000",
         "feeAmount": "26200000000000",
         "feeTokenSymbol": "ETH",
         "hash": "0x020fbe9eee00c1fd9dc1356b5cd01949ce844f1a65428b295b00559fe08dbf3f",
         "id": 383387,
         "memo": "test 1003 token(1) transfer from hello_loopring",
         "progress": "100%",
         "receiver": 10032,
         "receiverAddress": "0xaa520c7f9674aab15e6d3a98a72a93eae6e751b0",
         "senderAddress": "0x2cbfa87779572103ffd97cbf0e26ce7a73bbec6f",
         "status": "processed",
         "symbol": "LRC",
         "timestamp": 1623941490045,
         "txType": "TRANSFER",
         "updatedAt": 1623941490171
       },
       {
         "amount": "100000000000000000000",
         "feeAmount": "26200000000000",
         "feeTokenSymbol": "ETH",
         "hash": "0x2a38b31988359f742c65b668853adaf82bade728f1faf8f0748283f853e83b59",
         "id": 383384,
         "memo": "test 1001 token(1) transfer from hello_loopring",
         "progress": "100%",
         "receiver": 10032,
         "receiverAddress": "0xaa520c7f9674aab15e6d3a98a72a93eae6e751b0",
         "senderAddress": "0x2cbfa87779572103ffd97cbf0e26ce7a73bbec6f",
         "status": "processed",
         "symbol": "LRC",
         "timestamp": 1623941473913,
         "txType": "TRANSFER",
         "updatedAt": 1623941474341
       }
     ]
   }
   ```

   ​	The`"status": "processed"`indicates the transfer `"0x2a38b31988359f742c65b668853adaf82bade728f1faf8f0748283f853e83b59"` is done.

