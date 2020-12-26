import hashlib
import hmac
import ujson
from copy import copy
from datetime import datetime, timedelta
from enum import Enum, Flag
from threading import Lock
from operator import itemgetter
from py_eth_sig_utils import utils as sig_utils
from py_eth_sig_utils.signing import v_r_s_to_signature
from random import randint
import re
import sys
from time import time, sleep
import urllib
from web3 import Web3

from trading.rest_client import RestClient, Request
from ethsnarks.eddsa import PureEdDSA, PoseidonEdDSA
from ethsnarks.field import FQ, SNARK_SCALAR_FIELD
from ethsnarks.poseidon import poseidon_params, poseidon
from v3explorer.ecdsa_utils import *
from v3explorer.eddsa_utils import *

LOOPRING_REST_HOST = "https://uat2.loopring.io"

class Security(Flag):
    NONE        = 0
    EDDSA_SIGN  = 1
    API_KEY     = 2
    ECDSA_AUTH  = 4

class SignatureType(Enum):
    ECDSA           = 0
    EDDSA           = 1
    HASH_APPROVED   = 2

class EthSignType:
    ILLEGAL     = "00"
    INVALID     = "01"
    EIP_712     = "02"
    ETH_SIGN    = "03"

class LoopringV3AmmSampleClient(RestClient):
    """
    LOOPRING REST API SAMPLE
    """

    LOOPRING_REST_HOST = LOOPRING_REST_HOST
    MAX_ORDER_ID = 1<<32

    def __init__(self):
        """"""
        super().__init__()
        # exported account
        self.api_key     = ""
        self.address     = ""
        self.publicKeyX  = ""
        self.publicKeyY  = ""
        self.accountId   = 0

        # self.web3 = Web3(Web3.HTTPProvider(eth_addr))
        # order related
        self.orderId     = [0] * 256
        self.offchainId     = [0] * 256
        self.time_offset = 0
        self.nonce      = 0

        self.ammPoolNames = {}
        self.ammPools = {}
        self.tokenIds = {}
        self.tokenNames = {}
        self.tokenDecimals = {}

        self.init(self.LOOPRING_REST_HOST)
        self.start()

    def connect(self, exported_secret : dict):
        """
        Initialize connection to LOOPRING REST server.
        """
        self.accountId  = exported_secret['accountId']
        self.address    = exported_secret['address']
        self.api_key    = exported_secret['apiKey']
        self.exchange   = exported_secret['exchange']
        self.ecdsaKey   = int(exported_secret['ecdsaKey'], 16).to_bytes(32, byteorder='big')
        self.eddsaKey   = exported_secret['eddsaKey']
        self.publicKeyX = exported_secret["publicKeyX"]
        self.publicKeyY = exported_secret["publicKeyY"]
        self.chainId    = exported_secret["chainId"]

        self.next_eddsaKey = None

        self.ammJoinfeeBips = 0.0015

        # align srv and local time
        self.query_time()
        self.query_market_config()
        self.get_account()
        self.get_apiKey()

        EIP712.init_env(name="Loopring Protocol",
                        version="3.6.0",
                        chainId=self.chainId,
                        verifyingContract=exported_secret['exchange'])
        sleep(7)

    def sign(self, request):
        """
        Generate LOOPRING signature.
        """
        security = request.data.pop("security", Security.NONE)
        if security == Security.NONE:
            if request.method == "POST":
                request.data = request.params
                request.params = {}
            return request

        path = request.path
        if request.params:
            if request.method in ["GET", "DELETE"]:
                path = request.path + "?" + urllib.parse.urlencode(request.params)
        else:
            request.params = dict()

        # request headers
        headers = {
            "Content-Type" : "application/json",
            "Accept"       : "application/json",
            "X-API-KEY"    : self.api_key,
        }
        if request.headers != None:
            headers.update(request.headers)

        if security & Security.EDDSA_SIGN:
            signer = UrlEddsaSignHelper(self.eddsaKey, LOOPRING_REST_HOST)
            signature = signer.sign(request)
            headers.update({"X-API-SIG": signature})
        elif security & Security.ECDSA_AUTH:
            headers.update({"X-API-SIG": request.data["X-API-SIG"]})
            pass

        request.path = path
        if request.method not in ["GET", "DELETE"]:
            request.data = ujson.dumps(request.data) if len(request.data) != 0 else request.params
            request.params = {}
        else:
            request.data = {}

        request.headers = headers

        # print(f"finish sign {request}")
        return request

    def query_srv_time(self):
        data = {
            "security": Security.NONE
        }

        response = self.request(
            "GET",
            headers={
                "Content-Type" : "application/json",
                "Accept"       : "application/json",
            },
            path="/api/v3/timestamp",
            data=data
        )
        json_resp = response.json()
        return json_resp['timestamp']

    def query_info(self, restPath):
        """"""
        data = {
            "security": Security.NONE
        }

        response = self.request(
            "GET",
            headers={
                "Content-Type" : "application/json",
                "Accept"       : "application/json",
            },
            path="/api/v3/" + restPath,
            data=data
        )
        json_resp = response.json()
        print(ujson.dumps(json_resp, indent=4, sort_keys=True))
        [self.query_amm_pool_balance(pool["address"]) for pool in json_resp["pools"]]

    def query_amm_pool_balance(self, poolAddress):
        """"""
        data = {
            "security": Security.NONE
        }

        response = self.request(
            "GET",
            headers={
                "Content-Type" : "application/json",
                "Accept"       : "application/json",
            },
            path="/api/v3/amm/balance",
            data=data,
            params={"poolAddress": poolAddress[2:]}
        )
        json_resp = response.json()
        print(json_resp)

    def query_time(self):
        """"""
        data = {
            "security": Security.NONE
        }

        self.add_request(
            "GET",
            path="/api/v3/timestamp",
            callback=self.on_query_time,
            data=data
        )

    def on_query_time(self, data, request):
        local_time = int(time() * 1000)
        server_time = int(data["timestamp"])
        self.time_offset = int((local_time - server_time) / 1000)

    def query_market_config(self):
        """
            query market token and contract config
        """
        data = {"security": Security.NONE}

        params = {}

        self.add_request(
            method="GET",
            path="/api/v3/exchange/tokens",
            callback=self.on_query_token,
            params=params,
            data=data
        )

    def on_query_token(self, data, request):
        """"""
        # print(f"on_query_token: {data}")
        for d in data:
            self.tokenIds[d['symbol']] = d['tokenId']
            self.tokenNames[d['tokenId']] = d['symbol']
            self.tokenDecimals[d['tokenId']] = d['decimals']
        # print(f"tokenIds success: {self.tokenIds}")
        # print(f"tokenNames success: {self.tokenNames}")
        # print(f"tokenDecimals success: {self.tokenDecimals}")
        self.query_amm_pools()

    def query_amm_pools(self):
        """"""
        data = {
            "security": Security.NONE
        }

        self.add_request(
            "GET",
            path="/api/v3/amm/pools",
            callback=self.on_query_amm_pools,
            data=data
        )

    def on_query_amm_pools(self, data, request):
        # print(f"on_query_amm_pools get response: {data}")
        ammPools = data["pools"]
        for pool in ammPools:
            EIP712.init_amm_env(pool['name'], pool['version'], self.chainId, pool['address'])
            tokens = pool['tokens']['pooled']
            tokens.append(pool['tokens']['lp'])
            for token_id in tokens:
                self.get_storageId(token_id)
            self.ammPools[pool['address']] = tuple(tokens)
            self.ammPoolNames[pool['name']] = pool['address']

    def get_account(self):
        """"""
        data = {
            "security": Security.API_KEY
        }

        self.add_request(
            "GET",
            path="/api/v3/account",
            callback=self.on_query_account,
            data=data,
            params = {
                "owner": self.address
            }
        )

    def on_query_account(self, data, request):
        # print(f"on_query_account get response: {data}")
        self.nonce = data['nonce']

    def get_user_data(self, dataType):
        """"""
        data = {
            "security": Security.API_KEY
        }

        self.add_request(
            "GET",
            path=f"/api/v3/user/{dataType}",
            callback=self.on_get_user_data,
            data=data,
            params = {
                "accountId": self.accountId
            },
            extra=dataType
        )

    def on_get_user_data(self, data, request):
        print(f"get user {request.extra} get response: {ujson.dumps(data, indent=4, sort_keys=True)}")

    def get_transfers(self):
        """"""
        self.get_user_data("transfers")

    def get_updates(self):
        """"""
        self.get_user_data("updateInfo")

    def get_creates(self):
        """"""
        self.get_user_data("createInfo")

    def get_trades(self):
        """"""
        self.get_user_data("trades")

    def get_orders(self):
        """"""
        data = {
            "security": Security.API_KEY
        }

        params = {
            "accountId": self.accountId,
            # "start" : 0,
            # "end" : 1700000000,
            # "status": "processing",
            # "limit" : 500
        }

        self.add_request(
            "GET",
            path=f"/api/v3/orders",
            callback=self.on_get_user_data,
            data=data,
            params = params,
            extra = self.accountId
        )

    def get_withdrawals(self):
        """"""
        self.get_user_data("withdrawals")

    def get_deposits(self):
        """"""
        self.get_user_data("deposits")

    def get_amm_txs(self):
        """"""
        data = {
            "security": Security.API_KEY
        }

        params = {
            "accountId": self.accountId,
        }

        self.add_request(
            "GET",
            path=f"/api/v3/amm/user/transactions",
            callback=self.on_get_user_data,
            data=data,
            params = params,
            extra = self.accountId
        )

    def get_apiKey(self):
        """"""
        data = {
            "security": Security.EDDSA_SIGN
        }

        self.add_request(
            "GET",
            path="/api/v3/apiKey",
            callback=self.on_get_apiKey,
            data=data,
            params = {
                "accountId": self.accountId,
            }
        )

    def on_get_apiKey(self, data, request):
        # print(f"on_get_apiKey get response: {data}")
        self.api_key = data["apiKey"]
        self.query_balance()

    def query_balance(self):
        """"""
        data = {"security": Security.API_KEY}

        param = {
            "accountId": self.accountId,
            "tokens": ','.join([str(token) for token in self.tokenIds.values()])
        }

        self.add_request(
            method="GET",
            path="/api/v3/user/balances",
            callback=self.on_query_balance,
            params=param,
            data=data
        )

    def on_query_balance(self, data, request):
        for balance in data:
            tokenAmount = balance['total']
            frozenAmount = balance['locked']
            pending = balance.get('pending', {"withdraw":"0","deposit":"0"})
            for token in self.tokenIds.values():
                if token == balance['tokenId']:
                    token_symbol = self.tokenNames[token]
                    decimals = self.tokenDecimals[token]
                    print(f"Account balance {token_symbol} : {float(tokenAmount)/(10**decimals)}, locked: {float(frozenAmount)/(10**decimals)}")

    def get_storageId(self, tokenSId):
        """"""
        data = {
            "security": Security.API_KEY
        }

        self.add_request(
            "GET",
            path="/api/v3/storageId",
            callback=self.on_get_storageId,
            data=data,
            params = {
                "accountId"     : self.accountId,
                "sellTokenId"   : tokenSId
            }
        )

    def on_get_storageId(self, data, request):
        tokenId = request.params['sellTokenId']
        self.orderId[tokenId] = data['orderId']
        self.offchainId[tokenId] = data['offchainId']
        # print(f" self.offchainId = { self.offchainId},  self.orderId = { self.orderId}")

    def update_account_ecdsa(self, privateKey, publicKey):
        """"""
        self.eddsaKey = hex(int(privateKey))
        self.publicKeyX = "0x" + hex(int(publicKey.x))[2:].zfill(64)
        self.publicKeyY = "0x" + hex(int(publicKey.y))[2:].zfill(64)
        req = {
            "publicKey" : {
                "x" : self.publicKeyX,
                "y" : self.publicKeyY,
            },
            "maxFee" : {
                "tokenId" : 0,
                "volume"  : "0"
            },
            'validUntil': 1700000000,
            'nonce': self.nonce
        }
        updateAccountReq = self._create_update_request(req)
        data = {"security": Security.ECDSA_AUTH}
        data.update(updateAccountReq)

        message = createUpdateAccountMessage(updateAccountReq)
        # print(f"message hash = {bytes.hex(message)}")
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712
        data['ecdsaSignature'] = data['X-API-SIG']
        # print(f"data = {data}")

        self.add_request(
            method="POST",
            path="/api/v3/account",
            callback=self.on_update_account,
            params=updateAccountReq,
            data=data,
            extra=updateAccountReq
        )

    def update_account_eddsa(self, privateKey, publicKey, approved=False):
        """"""
        assert self.eddsaKey is not None and privateKey is not None
        self.next_eddsaKey = hex(int(privateKey))
        req = {
            "publicKey" : {
                "x" : '0x' + hex(int(publicKey.x))[2:].zfill(64),
                "y" : '0x' + hex(int(publicKey.y))[2:].zfill(64),
            },
            "maxFee" : {
                "tokenId" : 0,
                "volume"  : "4000000000000000"
            },
            'validUntil': 1700000000,
            'nonce': self.nonce
        }
        updateAccountReq = self._create_update_request(req)
        # print(f"create new order {order}")
        data = {"security": Security.ECDSA_AUTH}
        data.update(updateAccountReq)

        message = createUpdateAccountMessage(updateAccountReq)
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712

        if not approved:
            signer = UpdateAccountEddsaSignHelper(self.eddsaKey)
            signedMessage = signer.sign(updateAccountReq)
            data.update({"eddsaSignature": signedMessage})

        # print(data)
        self.add_request(
            method="POST",
            path="/api/v3/account",
            callback=self.on_update_account,
            params=updateAccountReq,
            data=data,
            extra=updateAccountReq
        )

    def _create_update_request(self, req):
        """"""
        return {
            "exchange" : self.exchange,
            "owner" : self.address,
            "accountId" : self.accountId,
            "publicKey" : req['publicKey'],
            "maxFee" :  req['maxFee'],
            "validUntil" : req['validUntil'],
            "nonce" : self.nonce
        }

    def on_update_account(self, data, request):
        """"""
        if data['status'] in ["processing", "processed"]:
            self.eddsaKey = self.next_eddsaKey
            self.next_eddsaKey = None
            publicKeyInfo = ujson.loads(request.data)
            self.publicKeyX = publicKeyInfo['publicKey']['x']
            self.publicKeyY = publicKeyInfo['publicKey']['y']
            print(f"on_update_account get response: {data}")

    def transfer_ecdsa(self, to_b, token, amount):
        """"""
        req = self._create_transfer_request(to_b, token, amount)
        # print(f"create new order {order}")
        data = {"security": Security.ECDSA_AUTH}

        data.update(req)

        message = createOriginTransferMessage(req)
        # print(f"transfer message hash = {bytes.hex(message)}")
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712
        data['ecdsaSignature'] = data['X-API-SIG']

        # print(f"data = {data}")
        self.add_request(
            method="POST",
            path="/api/v3/transfer",
            callback=self.on_transfer,
            params=req,
            data=data,
            extra=req
        )

    def transfer_eddsa(self, to_b, token, amount, validUntil=None, storageId=None, approved=False):
        """"""
        req = self._create_transfer_request(to_b, token, amount, validUntil, storageId)
        # print(f"create new req {req}")
        data = {"security": Security.ECDSA_AUTH}
        data.update(req)

        signer = OriginTransferEddsaSignHelper(self.eddsaKey)
        signedMessage = signer.sign(req)
        if not approved:
            data.update({"eddsaSignature": signedMessage})

        message = createOriginTransferMessage(req)
        # print(f"transfer message hash = {bytes.hex(message)}")
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712

        self.add_request(
            method="POST",
            path="/api/v3/transfer",
            callback=self.on_transfer,
            params=req,
            data=data,
            extra=req
        )

    def _create_transfer_request(self, to_b, token, amount, validUntil = None, storageId = None):
        """"""
        tokenId = self.tokenIds[token]
        decimalUnit = 10**self.tokenDecimals[tokenId]
        if storageId is None:
            storageId = self.offchainId[tokenId]
            self.offchainId[tokenId] += 2

        return {
            "exchange": self.exchange,
            "payerId": self.accountId,
            "payerAddr": self.address,
            "payeeId": 0,
            "payeeAddr": to_b,
            "token": {
                "tokenId": tokenId,
                "volume": str(int(amount*decimalUnit))
            },
            "maxFee" : {
                "tokenId": tokenId,
                "volume": str(int(amount*decimalUnit/1000))
            },
            "storageId": storageId,
            "validUntil": int(time()) + 60 * 60 * 24 * 60 if validUntil is None else validUntil,
            "memo": f"test {storageId} token({tokenId}) transfer from hello_loopring"
        }

    def on_transfer(self, data, request):
        """"""
        print(f"on_transfer get response: {data}")

    def offchainWithdraw_ecdsa(self, to_b, token, amount, minGas):
        """"""
        data = {"security": Security.ECDSA_AUTH}
        req = self._create_offchain_withdraw_request(to_b, token, amount, minGas, bytes(0))
        # print(f"create new order {order}")
        data.update(req)

        message = createOffchainWithdrawalMessage(req)
        # print(f"withdraw message hash = {bytes.hex(message)}")
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712
        data['ecdsaSignature'] = data['X-API-SIG']

        self.add_request(
            method="POST",
            path="/api/v3/user/withdrawals",
            callback=self.on_withdraw,
            params=req,
            data=data,
            extra=req
        )

    def offchainWithdraw_eddsa(self, to_b, token, amount, minGas,
                                extraData=bytes(0), validUntil=None, storageId=None):
        """"""
        data = {"security": Security.ECDSA_AUTH}
        req = self._create_offchain_withdraw_request(to_b, token, amount, minGas, extraData, validUntil, storageId)
        data.update(req)

        signer = WithdrawalEddsaSignHelper(self.eddsaKey)
        # print(f"request eddsa hash = {signer.hash(req)}")
        signedMessage = signer.sign(req)
        data.update({"eddsaSignature": signedMessage})

        message = createOffchainWithdrawalMessage(req)
        # print(f"withdraw message hash = {bytes.hex(message)}")
        v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
        data['X-API-SIG'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712

        self.add_request(
            method="POST",
            path="/api/v3/user/withdrawals",
            callback=self.on_withdraw,
            params=req,
            data=data,
            extra=req
        )

    def _create_offchain_withdraw_request(self, to: str, token, amount: float, minGas: int,
                                            extraData=bytes(0), validUntil=None, storageId=None):
        """"""
        tokenId = self.tokenIds[token]
        decimalUnit = 10**self.tokenDecimals[tokenId]
        toAddr = self.address if to == "" else to
        onchainDataHash = Web3.keccak(b''. join([int(minGas).to_bytes(32, 'big'),
                                                 int(toAddr, 16).to_bytes(20, 'big'),
                                                 extraData]))[:20]
        if storageId is None:
            storageId = self.offchainId[tokenId]
            self.offchainId[tokenId] += 2

        return {
            "exchange": self.exchange,
            "accountId": self.accountId,
            "owner": self.address,
            "token": {
                "tokenId": tokenId,
                "volume": str(int(amount*decimalUnit))
            },
            "maxFee" : {
                "tokenId": tokenId,
                "volume": str(int(amount*decimalUnit/1000))
            },
            "to": toAddr,
            "onChainDataHash": "0x" + bytes.hex(onchainDataHash),
            "storageId": storageId,
            "validUntil" : int(time()) + 60 * 60 * 24 * 60 if validUntil is None else validUntil,
            "minGas": minGas,
            "extraData": bytes.hex(extraData)
        }

    def on_withdraw(self, data, request):
        """"""
        print(f"{request} get response: {data}")

    def send_order(self, base_token, quote_token, buy, price, volume, ammPoolAddress = None):
        order = self._create_order(base_token, quote_token, buy, price, volume, ammPoolAddress)
        # print(f"create new order {order}")
        data = {"security": Security.API_KEY}
        headers = {
            "Content-Type": "application/json",
        }
        data.update(order)
        self.add_request(
            method="POST",
            path="/api/v3/order",
            callback=self.on_send_order,
            params=order,
            data=data,
            extra=order
        )

    def _create_order(self, base_token, quote_token, buy, price, volume, ammPoolAddress):
        if buy:
            tokenSId = self.tokenIds[quote_token]
            tokenBId = self.tokenIds[base_token]
            amountS = str(int(10 ** self.tokenDecimals[tokenSId] * price * volume))
            amountB = str(int(10 ** self.tokenDecimals[tokenBId] * volume))
        else:
            tokenSId = self.tokenIds[base_token]
            tokenBId = self.tokenIds[quote_token]
            amountS = str(int(10 ** self.tokenDecimals[tokenSId] * volume))
            amountB = str(int(10 ** self.tokenDecimals[tokenBId] * price * volume))

        orderId = self.orderId[tokenSId]
        assert orderId < self.MAX_ORDER_ID
        self.orderId[tokenSId] += 2

        # order base
        order = {
            # sign part
            "exchange"      : self.exchange,
            "accountId"     : self.accountId,
            "storageId"     : orderId,
            "sellToken": {
                "tokenId": tokenSId,
                "volume": amountS
            },
            "buyToken" : {
                "tokenId": tokenBId,
                "volume": amountB
            },
            "validUntil"    : 1700000000,
            "maxFeeBips"    : 50,
            "fillAmountBOrS": buy,
            # "taker"         : "0000000000000000000000000000000000000000",
            # aux data
            "allOrNone"     : False,
            "clientOrderId" : "SampleOrder-" + str(int(time()*1000)),
            "orderType"     : "LIMIT_ORDER"
        }

        if ammPoolAddress is not None:
            assert ammPoolAddress in self.ammPools
            assert tokenSId in self.ammPools[ammPoolAddress]
            assert tokenBId in self.ammPools[ammPoolAddress]
            order["poolAddress"] = ammPoolAddress
            order["orderType"]   = "AMM"
            order["fillAmountBOrS"] = False

        signer = OrderEddsaSignHelper(self.eddsaKey)
        msgHash = signer.hash(order)
        signedMessage = signer.sign(order)
        # update signaure
        order.update({
            "hash"     : str(msgHash),
            "eddsaSignature" : signedMessage
        })
        return order

    def on_send_order(self, data, request):
        print(f"{data}\nplace order success: hash={data['hash']}, clientOrderId={request.extra['clientOrderId']}")

    def cancel_order(self, **kwargs):
        """"""
        data = {
            "security": Security.EDDSA_SIGN
        }

        params = {
            "accountId": self.accountId,
        }
        if "orderHash" in kwargs:
            params['orderHash'] = kwargs['orderHash']
        elif "clientOrderId" in kwargs:
            params['clientOrderId'] = kwargs['clientOrderId']

        # print(params)
        self.add_request(
            method="DELETE",
            path="/api/v3/order",
            callback=self.on_cancel_order,
            params=params,
            data=data,
        )

    def on_cancel_order(self, data, request):
        """"""
        print(f"on_cancel_order {data} {request.data}")
        pass

    def join_amm_pool(self, poolName, tokenAmounts, mintMinAmount, validUntil=None, storageIds=None, sigType=SignatureType.EDDSA):
        data = {"security": Security.API_KEY}
        req = self._create_join_pool_request(poolName, tokenAmounts, mintMinAmount, validUntil, storageIds)
        data.update(req)

        message = createAmmPoolJoinMessage(req)
        # print(f"join message hash = {bytes.hex(message)}")
        if sigType == SignatureType.ECDSA:
            v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
            data['ecdsaSignature'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712
        elif sigType == SignatureType.EDDSA:
            signer = MessageHashEddsaSignHelper(self.eddsaKey)
            data['eddsaSignature'] = signer.sign(message)

        self.add_request(
            method="POST",
            path="/api/v3/amm/join",
            callback=self.on_join_pool,
            params=req,
            data=data,
            extra=req
        )

    def _create_join_pool_request(self, poolName, joinAmounts, mintMinAmount, validUntil = None, storageIds = None):
        poolAddress = self.ammPoolNames[poolName]
        tokenAId, tokenBId = self.ammPools[poolAddress][:2]
        poolTokenId = self.ammPools[poolAddress][2]
        mintMinAmount = str(int(mintMinAmount * 10**self.tokenDecimals.get(poolTokenId, 8)))
        req = {
            'poolAddress': poolAddress,
            'owner': self.address,
            "joinTokens" : {
                "pooled" : [
                    {
                        "tokenId": tokenAId,
                        "volume" : str(int(joinAmounts[0] * 10**self.tokenDecimals[tokenAId]))
                    },
                    {
                        "tokenId": tokenBId,
                        "volume" : str(int(joinAmounts[1] * 10**self.tokenDecimals[tokenBId]))
                    },
                ],
                "minimumLp" : {
                    "tokenId" : poolTokenId,
                    "volume"  : mintMinAmount
                }
            },
            'storageIds': [self.offchainId[tokenAId], self.offchainId[tokenBId]] if storageIds is None else storageIds,
            'validUntil': 1700000000
        }

        if storageIds is None:
            self.offchainId[tokenAId]+=2
            self.offchainId[tokenBId]+=2
        return req

    def on_join_pool(self, data, request):
        print(f"PoolJoin success: hash={data['hash']}")

    def exit_amm_pool(self, poolName, burnAmount, exitMinAmounts, sigType=SignatureType.EDDSA):
        data = {"security": Security.API_KEY}
        req = self._create_exit_pool_request(poolName, burnAmount, exitMinAmounts)
        # print(f"create new order {order}")
        data.update(req)

        message = createAmmPoolExitMessage(req)
        # print(f"join message hash = {bytes.hex(message)}")
        if sigType == SignatureType.ECDSA:
            v, r, s = sig_utils.ecsign(message, self.ecdsaKey)
            data['ecdsaSignature'] = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + EthSignType.EIP_712
        elif sigType == SignatureType.EDDSA:
            signer = MessageHashEddsaSignHelper(self.eddsaKey)
            data['eddsaSignature'] = signer.sign(message)

        self.add_request(
            method="POST",
            path="/api/v3/amm/exit",
            callback=self.on_exit_pool,
            params=req,
            data=data,
            extra=req
        )

    def _create_exit_pool_request(self, poolName, burnAmount, exitMinAmounts):
        poolAddress = self.ammPoolNames[poolName]
        tokenAId, tokenBId = self.ammPools[poolAddress][:2]
        poolTokenId = self.ammPools[poolAddress][2]
        burnAmount = str(int(burnAmount * 10**self.tokenDecimals.get(poolTokenId, 18)))
        req = {
            'poolAddress': poolAddress,
            'owner': self.address,
            "exitTokens" : {
                "unPooled" : [
                    {
                        "tokenId": tokenAId,
                        "volume" : str(int(exitMinAmounts[0] * 10**self.tokenDecimals[tokenAId]))
                    },
                    {
                        "tokenId": tokenBId,
                        "volume" : str(int(exitMinAmounts[1] * 10**self.tokenDecimals[tokenBId]))
                    },
                ],
                "burned" : {
                    "tokenId" : poolTokenId,
                    "volume"  : burnAmount
                }
            },
            'storageId': self.offchainId[poolTokenId],
            'maxFee': str(int(int(exitMinAmounts[1])*0.002)),
            'validUntil': 1700000000
        }
        self.offchainId[poolTokenId]+=2
        return req

    def on_exit_pool(self, data, request):
        print(f"PoolExit success: hash={data['hash']}")

if __name__ == "__main__":
    loopring_rest_sample = LoopringV3AmmSampleClient()
    srv_time = loopring_rest_sample.query_srv_time()
    print(f"srv time is {srv_time}")
