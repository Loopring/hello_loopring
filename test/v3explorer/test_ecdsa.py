import unittest
from py_eth_sig_utils import utils as sig_utils
from py_eth_sig_utils.signing import v_r_s_to_signature, signature_to_v_r_s
from web3 import Web3

from v3explorer.ecdsa_utils import *
from v3explorer.loopring_v3_client import LoopringV3AmmSampleClient
from time import time

class TestApiSigns(unittest.TestCase):
    def setUp(self):
        "Hook method for setting up the test fixture before exercising it."
        EIP712.init_env(name="Loopring Protocol",
                        version="3.6.0",
                        chainId=5,
                        verifyingContract="0x2FFfAa5D860B39b28467863a4454EE874127eF5E")
        
        EIP712.init_amm_env(name="pool-lrc-eth",
                            version="1.0.0",
                            chainId=1,
                            verifyingContract="0x0000000000000000000000000000000000000001")

        pass

    def test_domain_separator(self):
        domainSep = EIP712.exchangeDomain.hash_struct()
        assert("0x" + bytes.hex(domainSep) == "0x0cf6ea7629bf5bc100a49a1508666d887795b6a97195eb205c6dafcd4fbe2328")

    def test_amm_domain_separator(self):
        EIP712.init_amm_env(name="AMM-YFI-ETH",
                    version="1.0.0",
                    chainId=1,
                    verifyingContract="0xd85f594481D3DEE61FD38464dD54CF3ccE6906b6")
        domainSep = EIP712.ammPoolDomains['0xd85f594481D3DEE61FD38464dD54CF3ccE6906b6'].hash_struct()
        print("0x" + bytes.hex(domainSep).zfill(64))

    def test_update_account_ecdsa_sig_uat(self):
        EIP712.init_env(name="Loopring Protocol",
                version="3.6.0",
                chainId=1337,
                verifyingContract="0x7489DE8c7C1Ee35101196ec650931D7bef9FdAD2")
        req = {
            'exchange': '0x7489DE8c7C1Ee35101196ec650931D7bef9FdAD2',
            'owner': "0x23a51c5f860527f971d0587d130c64536256040d",
            'accountId': 10004,
            "publicKey" : {
                "x" : '0x2442c9e22d221abac0582cf764028d21114c9676b743f590741ffdf1f8a735ca',
                "y" : '0x08a42c954bc114b967bdd77cf7a1780e07fe10a4ebbef00b567ef2876e997d1a'
            },
            "maxFee" : {
                "tokenId" : 0,
                "volume"  : "4000000000000000"
            },
            'validUntil': 1700000000,
            'nonce': 1
        }
        hash = createUpdateAccountMessage(req)
        # print('createUpdateAccountMessage hash = 0x'+bytes.hex(hash))
        assert('0x'+bytes.hex(hash) == "0x031fac4223887173ca741460e3b1e642d9d73371a64cd42b46212cc159877f03")

    def test_transfer_ecdsa_sig(self):
        EIP712.init_env(name="Loopring Protocol",
                version="3.6.0",
                chainId=1,
                verifyingContract="0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9")
        req = {
            "exchange": "0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9",
            "payerId": 0,
            "payerAddr": "0x611db73454c27e07281d2317aa088f9918321415",
            "payeeId": 0,
            "payeeAddr": "0xc0ff3f78529ab90f765406f7234ce0f2b1ed69ee",
            "token": {
                "tokenId": 0,
                "volume": str(1000000000000000000),
            },
            "maxFee" : {
                "tokenId": 0,
                "volume": str(1000000000000000),
            },
            "storageId": 1,
            "validUntil": 0xfffffff
        }
        hash = createOriginTransferMessage(req)
        print('createOriginTransferMessage hash = 0x'+bytes.hex(hash))
        assert('0x'+bytes.hex(hash) == "0xcf3965e3eab3a47b1712b9cf8c7caa1af1a55a2e7a61869455ff64c6d9c791d1")
        v, r, s = sig_utils.ecsign(hash, int("1", 16).to_bytes(32, byteorder='big'))
        print(f"sig = {'0x' + bytes.hex(v_r_s_to_signature(v, r, s))}")
        # sig == v, r, s
        # assert(sig[0] == 27)
        # assert(sig[1] == 0x02d5ce917a2981c790f7e383f92c01735dd209d77d0b5ec422eec6207c5c486c)
        # assert(sig[2] == 0x72067b3c2501fb95674825933029d257f16f1955c200d3bb5162dfcc5dfd39d6)

    def test_withdraw_ecdsa_sig(self):
        EIP712.init_env(name="Loopring Protocol",
                version="3.6.0",
                chainId=1,
                verifyingContract="0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9")
        extraData = bytes(0)
        onchainData = b''. join([int("0").to_bytes(32, 'big'),
                                            int("0x15127e64b546c5d0a9713d0b086e66a3359d8f6b", 16).to_bytes(20, 'big'),
                                            extraData])
        onchainDataHash = Web3.keccak(onchainData)[:20]
        print(f"onchainData = {bytes.hex(onchainData)}, onchainDataHash = {'0x'+bytes.hex(onchainDataHash)}")
        req = {
            "exchange": "0x35990C74eB567B3bbEfD2Aa480467b1031b23eD9",
            "accountId": 5,
            "owner": "0x611db73454c27e07281d2317aa088f9918321415",
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
        hash = createOffchainWithdrawalMessage(req)
        print('createOffchainWithdrawalMessage hash = 0x'+bytes.hex(hash))
        assert('0x'+bytes.hex(hash) == "0xfae5a78e3d12d2c8b220ab8ae7bf733120285699c2c4441972986044c02cbb06")
        v, r, s = sig_utils.ecsign(hash, int("1", 16).to_bytes(32, byteorder='big'))
        print(f"sig = {'0x' + bytes.hex(v_r_s_to_signature(v, r, s))}")

    def test_amm_join_ecdsa_sig_1(self):
        EIP712.init_amm_env(name="AMM Pool LRC-ETH",
                    version="1.0.0",
                    chainId=5,
                    verifyingContract="0xDadF20fc684C11ce9a8713C7fdd496865562764f")
        req = {
            'poolAddress': "0xd95EE4302E49963CB751945c48BD553fd093",
            'owner': "0x23a51c5f860527f971d0587d130c64536256040d",
            "joinTokens" : {
                "pooled" : [
                    {
                        "tokenId": 1,
                        "volume" : "100000000000000000000"
                    },
                    {
                        "tokenId": 0,
                        "volume" : "100000000000000000000"
                    },
                ],
                "minimumLp" : {
                    "tokenId" : 5,
                    "volume"  : "100000000000"
                }
            },
            'storageIds': [1,1],
            'validUntil': 1700000000
        }
        hash = createAmmPoolJoinMessage(req)
        print('createAmmPoolJoinMessage hash = 0x'+bytes.hex(hash))
        # assert('0x'+bytes.hex(hash) == "0xbfda6876a7fedf9f6403000d306f41bcc5e8c10330aedb99d4503f866efbc895")
        v, r, s = sig_utils.ecsign(hash, int("0x4c5496d2745fe9cc2e0aa3e1aad2b66cc792a716decf707ddb3f92bd2d93ad24", 16).to_bytes(32, byteorder='big'))
        print(f"sig = {'0x' + bytes.hex(v_r_s_to_signature(v, r, s))}")

    def test_amm_exit_ecdsa_sig(self):
        EIP712.init_amm_env(name="pool-lrc-eth",
                    version="1.0.0",
                    chainId=1,
                    verifyingContract="0xd95EE4302E49963CB751945c48BD553fd093")
        req = {
            'poolAddress': "0xd95EE4302E49963CB751945c48BD553fd093",
            'owner': "0x23a51c5f860527f971d0587d130c64536256040d",
            "exitTokens" : {
                "unPooled" : [
                    {
                        "tokenId": 1,
                        "volume" : "100000000000000000000"
                    },
                    {
                        "tokenId": 0,
                        "volume" : "100000000000000000000"
                    },
                ],
                "burned" : {
                    "tokenId" : 5,
                    "volume"  : "100000000000"
                }
            },
            'storageId': 1,
            'maxFee': "1000000000",
            'validUntil': 1700000000
        }
        hash = createAmmPoolExitMessage(req)
        print('createAmmPoolExitMessage hash = 0x'+bytes.hex(hash))
        assert('0x'+bytes.hex(hash) == "0x3a4fbd83181adf60cfdc176e25eddc761e069553eb72de7022d3165b43b08dd4")
        v, r, s = sig_utils.ecsign(hash, int("1", 16).to_bytes(32, byteorder='big'))
        print(f"sig = {'0x' + bytes.hex(v_r_s_to_signature(v, r, s))}")
    
    def test_hw_wallet_ecdsa_sign_1(self):
        ecdsaSig = "0xf3fde24c40614bd48d22ab005bb9b57215ff77d390744aa145cbb6a7004532584bd4ecdde4cf1b5df5ed0e518b01cfad79a84cd50a457f524ff42b50c1b715691b"
        owner = "0x6b1029c9ae8aa5eea9e045e8ba3c93d380d5bdda"
        v, r, s = signature_to_v_r_s(bytes.fromhex(ecdsaSig.replace("0x", "")))
        origin_message = "0xc53367f8714c5cbb86b39de72f9010a11564948dc72f7dfad6f9007efae98802"
        origin_message_bytes = bytes.fromhex(origin_message.replace("0x", ""))
        # message_toSign = Web3.keccak(b"\x19Ethereum Signed Message:\n" + bytes(f"{len(origin_message_bytes)}", 'utf8') + origin_message_bytes)
        k = sig_utils.ecrecover_to_pub(origin_message_bytes, v, r, s)
        address = Web3.keccak(k)[-20:].hex()
        assert(address.lower() == owner)

    def test_hw_wallet_ecdsa_sign_2(self):
        ecdsaSig = "0xb726f15413de8be5756a50b261c92a9689c5e45301ceafc2f4498984a57b51f27355ae7084c1701668ac44dbebca9158b8c92a16eb7dd6fe9b98d72896b54fce1b"
        owner = "0x2ca1ac470909bee7f83b432348787ca8df800131"
        v, r, s = signature_to_v_r_s(bytes.fromhex(ecdsaSig.replace("0x", "")))
        origin_message = "1"
        origin_message_bytes = bytes(origin_message, 'utf-8')
        message_toSign = Web3.keccak(b"\x19Ethereum Signed Message:\n" + bytes(f"{len(origin_message_bytes)}", 'utf8') + origin_message_bytes)
        k = sig_utils.ecrecover_to_pub(message_toSign, v, r, s)
        address = Web3.keccak(k)[-20:].hex()
        assert(address.lower() == owner)

if __name__ == '__main__':
    unittest.main()
