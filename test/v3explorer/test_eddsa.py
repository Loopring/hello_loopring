import pytest
import unittest
from web3 import Web3

from sdk.loopring_v3_client import LOOPRING_REST_HOST
from sdk.sig_utils.eddsa_utils import *
from sdk.ethsnarks.jubjub import Point
from sdk.ethsnarks.eddsa import Signature, SignedMessage
from time import time
from sdk.request_utils.rest_client import Request

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
        signer = UrlEddsaSignHelper("0x1234", LOOPRING_REST_HOST)
        url = urllib
        request = Request(
            method="GET",
            path="/api/v3/apiKey",
            params={"accountId": 10001},
            data={},
            headers={}
            )
        hash = signer.hash(request)
        print(f"hash = {hex(hash)}")

        signedMessage = signer.sign(request)
        print(f"signedMessage = {signedMessage}")

        signature = signer.sigStrToSignature("0x0dfbbcc409fbcdb07dc350b50cf034fa0ebfd259346c81b3fd3bdb8951117a152ccecf37615e470d0038f15fd1c1ea69f212636033d880119b474e1e9e7548131074a9dad709b4e4950a86fea510d9c0b207a66f35aab4fc135e5fe64b9d009b")
        signedMessage = SignedMessage(
            PoseidonEdDSA.B() * 0x1234,
            signature,
            hash
        )
        assert signer.verify(signedMessage.msg, signedMessage)

    def test_updateAccount_eddsa_hash(self):
        req = {
            "exchange": "0x80eB675C448602284a3e2090d873aF2af0450Fd9",
            'owner': "0x3fce664c0a76b1f91ae9ad767545bec70875bf71",
            'accountId': 10001,
            "publicKey" : {
                "x" : "0x2ea2c249f7ffa335363ecbfbfe07a73268e5565ecaa9468e1140410f1349e16a",
                "y" : "0x10da55ef2a7235bb192d47554f4d3d5091d6854b686471270d5c3838b3ed733c",
            },
            "maxFee" : {
                "tokenId" : 0,
                "volume"  : "4000000000000000"
            },
            'validUntil': 1700000000,
            'nonce': 2
            }
        signer = UpdateAccountEddsaSignHelper("0x623167b48a61c02c546fef1bb0d810f4c0d14802b7669ef5b9de9af83212de")
        hash = signer.hash(req)
        print(f"hash = {hex(hash)}")

        signedMessage = signer.sign(req)
        print(f"signedMessage = {signedMessage}")

        signature = signer.sigStrToSignature(signedMessage)
        signedMessage = SignedMessage(
            PoseidonEdDSA.B() * 0x623167b48a61c02c546fef1bb0d810f4c0d14802b7669ef5b9de9af83212de,
            signature,
            hash
        )
        assert signer.verify(signedMessage.msg, signedMessage)

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
        key = "0x5"
        signer = MessageHashEddsaSignHelper(key)
        msg = "0xABCD1234"
        hash  = signer.hash(msg)
        assert hash == 360292934

        sigStr = ("0x02c8188eae892aab8156d117fb3b00cea67cdcf2e7c58eea75ac422bd0921417095bfe981854b2c56972f2343e717b293731de7d43984dacb9e91e9767f0581b1de6fbe479d71c7ee016595c0ad62c9fc7b31b52fd7dcbcc259c86ac2f04f09d")
        signature = signer.sigStrToSignature(sigStr)
        signedMessage = SignedMessage(
            PoseidonEdDSA.B() * int(key, 16),
            signature,
            360292934
        )
        assert signer.verify(signedMessage.msg, signedMessage)

if __name__ == "__main__":
    unittest.main()
