import pytest
import unittest
from web3 import Web3

from v3explorer.eddsa_utils import *
from v3explorer.loopring_v3_client import LOOPRING_REST_HOST
from trading.rest_client import Request
from ethsnarks.jubjub import Point
from ethsnarks.eddsa import Signature, SignedMessage
from v3explorer.loopring_v3_client import LoopringV3AmmSampleClient
from time import time

class TestEddsaSignHelpers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        privKey, publicKey = PoseidonEdDSA.random_keypair()
        cls.privKey = hex(int(privKey))
        cls.publicKey = publicKey
        print(f"setUpClass: priv = {cls.privKey}")

    def test_order_signer_helper(self):
        signer = DummyEddsaSignHelper(private_key = self.privKey)
        data = {"data": 5}
        msg = signer.hash(data)
        sig = signer.sign(data)
        signature = signer.sigStrToSignature(sig)
        generatedSig = SignedMessage(Point(self.publicKey.x, self.publicKey.y), signature, msg)
        assert signer.verify(data, generatedSig)

    def test_url_signer(self):
        signer = UrlEddsaSignHelper(1, LOOPRING_REST_HOST)
        url = urllib
        request = Request(
            method="GET",
            path="/api/v2/apiKey",
            params={"accountId": 10010},
            data={},
            headers={}
            )
        hash = signer.hash(request)
        print(hash)

    def test_updateAccount_eddsa_hash(self):
        req = {
            "exchange": "0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9",
            'owner': "0xd854872f17c2783ae9d89e7b2a29cd72ec2a74ff",
            'accountId': 10,
            "publicKey" : {
                "x" : hex(int(self.publicKey.x)),
                "y" : hex(int(self.publicKey.y)),
            },
            "maxFee" : {
                "tokenId" : 0,
                "volume"  : "4000000000000000"
            },
            'validUntil': 1700000000,
            'nonce': 3
            }
        signer = UpdateAccountEddsaSignHelper(1)
        hash = signer.hash(req)
        print(f"hash = {hash}")

    def test_withdraw_eddsa_sig(self):
        extraData = bytes(0)
        onchainData = b''. join([int("0").to_bytes(32, 'big'),
                                int("0x23a51c5f860527f971d0587d130c64536256040d", 16).to_bytes(20, 'big'),
                                extraData])
        onchainDataHash = Web3.keccak(onchainData)[:20]
        assert('0x' + bytes.hex(onchainDataHash) == "0x09b0a56ec6c45c6f3af2abbdefd66b6e84bce8e4")

        # print(f"onchainData = {bytes.hex(onchainData)}, onchainDataHash = {'0x'+bytes.hex(onchainDataHash)}")
        req = {
            "exchange": "0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9",
            "accountId": 5,
            "owner": "0x23a51c5f860527f971d0587d130c64536256040d",
            "token": {
                "tokenId": 0,
                "volume": str(1000000000000000000),
            },
            "maxFee" : {
                "tokenId": 0,
                "volume": str(1000000000000000),
            },
            "to": "0xc0ff3f78529ab90f765406f7234ce0f2b1ed69ee",
            "onChainDataHash": "0x" + bytes.hex(onchainDataHash),
            "storageId": 5,
            "validUntil" : 0xfffffff,
            "minGas": 300000,
            "extraData": bytes.hex(extraData)
        }
        signer = WithdrawalEddsaSignHelper("0x4a3d1e098350")
        hash = signer.hash(req)
        assert(hex(hash) == "0x1c59c63f9bf24d97195d64d828af72e2037a4022413804e410799682d960f09c")

    def test_order_eddsa_sig(self):
        order = {
            # sign part
            "exchange"      : "0x7489DE8c7C1Ee35101196ec650931D7bef9FdAD2",
            "accountId"     : 10004,
            "storageId"     : 0,
            "sellToken": {
                "tokenId": 0,
                "volume": "90000000000000000000"
            },
            "buyToken" : {
                "tokenId": 1,
                "volume": "100000000000000000000"
            },
            "validUntil"    : 1700000000,
            "maxFeeBips"    : 50,
            "fillAmountBOrS": True,
            # "taker"         : "0000000000000000000000000000000000000000",
            # aux data
            "allOrNone"     : False,
            "clientOrderId" : "SampleOrder-" + str(int(time()*1000)),
            "orderType"     : "LIMIT_ORDER"
        }

        signer = OrderEddsaSignHelper(hex(56869496543825))
        msgHash = signer.hash(order)
        signedMessage = signer.sign(order)
        print(f"msgHash = {hex(msgHash)}")
        # print(f"signedMessage = {signedMessage}")

    def test_ocdh(self):
        onchainDataHash = Web3.keccak(b''. join([int("0").to_bytes(32, 'big'),
                                                 int("0x23A51c5f860527F971d0587d130c64536256040D", 16).to_bytes(20, 'big'),
                                                 bytes(0)]))
        print(bytes.hex(onchainDataHash[:20]))
        assert(bytes.hex(onchainDataHash[:20]) == "09b0a56ec6c45c6f3af2abbdefd66b6e84bce8e4")

    def test_hash_signer(self):
        key = "0x4c388978a9cd17ff7171fb8694fb7618c8bf48e7c800e81277870c6bf12e47b"
        signer = MessageHashEddsaSignHelper(key)
        sigStr = ("0x0c5213cf2f0efdbea23a3b3460317d044559c15856a6521231ecfcf068c0a0bd"
                 "1f19d3431ffbedcf8a8a7c8ba369f6e151eadb4c9bb8784b24d421b8b78c8daa"
                 "04e744f347d8f4ac654c62f05003bed7a963cabc5a511d6c28b8fcba5729137f")
        signature = signer.sigStrToSignature(sigStr)
        signedMessage = SignedMessage(
            PoseidonEdDSA.B() * int(key, 16),
            signature,
            int('0x16eedf96af3fa2f77ffddd58e6266f8ef1ec76465f7f04f3ef7cc3039f51421a', 16)
        )
        print(f"signedMessage = {signedMessage}")
        assert signer.verify(signedMessage.msg, signedMessage)

if __name__ == "__main__":
    unittest.main()
