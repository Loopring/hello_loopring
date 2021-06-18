import eip712_structs
from eip712_structs import EIP712Struct, Address, Array, Boolean, Bytes, Int, String, Uint
from eth_abi import encode_single, encode_abi
from py_eth_sig_utils import utils as sig_utils
from web3 import Web3
from sdk.ethsnarks.jubjub import Point
from sdk.ethsnarks.field import FQ


class EIP712:
    EIP191_HEADER = bytes.fromhex("1901")

    ammPoolDomains = {}

    @classmethod
    def init_env(cls, name, version, chainId, verifyingContract):
        cls.exchangeDomain = eip712_structs.make_domain(name = name,
                                                    version=version,
                                                    chainId=chainId,
                                                    verifyingContract=verifyingContract)
        # eip712_structs.default_domain = cls.exchangeDomain

    @classmethod
    def init_amm_env(cls, name, version, chainId, verifyingContract):
        cls.ammPoolDomains[verifyingContract] = eip712_structs.make_domain(name = name,
                                                                        version=version,
                                                                        chainId=chainId,
                                                                        verifyingContract=verifyingContract)
        # eip712_structs.default_domain = cls.exchangeDomain


    @classmethod
    def hash_packed(cls, domainHash, dataHash):
        # print(f"domainHash = {bytes.hex(domainHash)}")
        # print(f"dataHash = {bytes.hex(dataHash)}")
        return Web3.keccak(
                            b''.join([
                                cls.EIP191_HEADER,
                                domainHash,
                                dataHash
                            ])
                        )

# EIP712.init_env()

def generateUpdateAccountEIP712Hash(req: dict):
    class AccountUpdate(EIP712Struct):
        owner = Address()
        accountID = Uint(32)
        feeTokenID = Uint(16)
        maxFee = Uint(96)
        publicKey = Uint(256)
        validUntil = Uint(32)
        nonce = Uint(32)

    pt = Point(FQ(int(req['publicKey']['x'], 16)), FQ(int(req['publicKey']['y'], 16)))
    publicKey = int.from_bytes(pt.compress(), "little")
    # print(f"publicKey = {publicKey}")

    # "AccountUpdate(address owner,uint32 accountID,uint16 feeTokenID,uint96 maxFee,uint256 publicKey,uint32 validUntil,uint32 nonce)"
    update = AccountUpdate(
        owner       = req['owner'], #bytes.fromhex(req['owner'].replace("0x", "")),
        accountID   = req['accountId'],
        feeTokenID  = req['maxFee']['tokenId'],
        maxFee      = int(req['maxFee']['volume']),
        publicKey   = publicKey,
        validUntil  = req['validUntil'],
        nonce       = req['nonce']
    )

    # print(f"update type hash = {bytes.hex(update.type_hash())}")
    return EIP712.hash_packed(
        EIP712.exchangeDomain.hash_struct(),
        update.hash_struct()
    )

def generateTransferEIP712Hash(req: dict):
    """
        struct Transfer
        {
            address from;
            address to;
            uint16  tokenID;
            uint    amount;
            uint16  feeTokenID;
            uint    fee;
            uint32  validUntil;
            uint32  storageID;
        }
    """
    class Transfer(EIP712Struct):
        pass

    setattr(Transfer, 'from', Address())
    Transfer.to           = Address()
    Transfer.tokenID      = Uint(16)
    Transfer.amount       = Uint(96)
    Transfer.feeTokenID   = Uint(16)
    Transfer.maxFee       = Uint(96)
    Transfer.validUntil   = Uint(32)
    Transfer.storageID    = Uint(32)

    # "Transfer(address from,address to,uint16 tokenID,uint96 amount,uint16 feeTokenID,uint96 maxFee,uint32 validUntil,uint32 storageID)"
    transfer = Transfer(**{
        "from"          : req['payerAddr'],
        "to"            : req['payeeAddr'],
        "tokenID"       : req['token']['tokenId'],
        "amount"        : int(req['token']['volume']),
        "feeTokenID"    : req['maxFee']['tokenId'],
        "maxFee"        : int(req['maxFee']['volume']),
        "validUntil"    : req['validUntil'],
        "storageID"     : req['storageId']
    })

    # print(f"transfer type hash = {bytes.hex(transfer.type_hash())}")
    return EIP712.hash_packed(
        EIP712.exchangeDomain.hash_struct(),
        transfer.hash_struct()
    )

def generateOffchainWithdrawalEIP712Hash(req: dict):
    """
        struct Withdrawal
        {
            address owner;
            uint32  accountID;
            uint16  tokenID;
            uint    amount;
            uint16  feeTokenID;
            uint    fee;
            address to;
            bytes32 extraDataHash;
            uint    minGas;
            uint32  validUntil;
            uint32  storageID;
        }

    """
    class Withdrawal(EIP712Struct):
        owner = Address()
        accountID = Uint(32)
        tokenID = Uint(16)
        amount = Uint(96)
        feeTokenID = Uint(16)
        maxFee = Uint(96)
        to = Address()
        extraData = Bytes()
        minGas = Uint()
        validUntil = Uint(32)
        storageID = Uint(32)

    # "Withdrawal(address owner,uint32 accountID,uint16 tokenID,uint96 amount,uint16 feeTokenID,uint96 maxFee,address to,bytes extraData,uint256 minGas,uint32 validUntil,uint32 storageID)"
    withdrawal = Withdrawal(**{
        "owner"         : req['owner'],
        "accountID"     : req['accountId'],
        "tokenID"       : req['token']['tokenId'],
        "amount"        : int(req['token']['volume']),
        "feeTokenID"    : req['maxFee']['tokenId'],
        "maxFee"        : int(req['maxFee']['volume']),
        "to"            : req['to'],
        "extraData"     : bytes.fromhex(req['extraData']),
        "minGas"        : int(req['minGas']),
        "validUntil"    : req['validUntil'],
        "storageID"     : req['storageId'],
    })

    # print(f"extraData hash = {bytes.hex(Web3.keccak(bytes.fromhex(req['extraData'])))}")
    # print(f"withdrawal type hash = {bytes.hex(withdrawal.type_hash())}")
    return EIP712.hash_packed(
        EIP712.exchangeDomain.hash_struct(),
        withdrawal.hash_struct()
    )

def generateAmmPoolJoinEIP712Hash(req: dict):
    """
        struct PoolJoin
        {
            address   owner;
            uint96[]  joinAmounts;
            uint32[]  joinStorageIDs;
            uint96    mintMinAmount;
            uint32    validUntil;
        }
    """
    class PoolJoin(EIP712Struct):
        owner           = Address()
        joinAmounts     = Array(Uint(96))
        joinStorageIDs  = Array(Uint(32))
        mintMinAmount   = Uint(96)
        validUntil      = Uint(32)

    # "PoolJoin(address owner,uint96[] joinAmounts,uint32[] joinStorageIDs,uint96 mintMinAmount,uint32 validUntil)"
    join = PoolJoin(
        owner           = req['owner'],
        joinAmounts     = [int(token['volume']) for token in req['joinTokens']['pooled']],
        joinStorageIDs  = [int(id) for id in req['storageIds']],
        mintMinAmount   = int(req['joinTokens']['minimumLp']['volume']),
        validUntil      = req['validUntil']
    )

    # print(f"PoolJoin type hash = {bytes.hex(join.type_hash())}")
    return EIP712.hash_packed(
        EIP712.ammPoolDomains[req['poolAddress']].hash_struct(),
        join.hash_struct()
    )

def generateAmmPoolExitEIP712Hash(req: dict):
    """
        struct PoolExit
        {
            address   owner;
            uint96    burnAmount;
            uint32    burnStorageID; // for pool token withdrawal from user to the pool
            uint96[]  exitMinAmounts;
            uint96    fee;
            uint32    validUntil;
        }
    """
    class PoolExit(EIP712Struct):
        owner           = Address()
        burnAmount      = Uint(96)
        burnStorageID   = Uint(32)
        exitMinAmounts  = Array(Uint(96))
        fee             = Uint(96)
        validUntil      = Uint(32)

    # "PoolExit(address owner,uint96 burnAmount,uint32 burnStorageID,uint96[] exitMinAmounts,uint96 fee,uint32 validUntil)"
    exit = PoolExit(
        owner           = req['owner'],
        burnAmount      = int(req['exitTokens']['burned']['volume']),
        burnStorageID   = int(req['storageId']),
        exitMinAmounts  = [int(token['volume']) for token in req['exitTokens']['unPooled']],
        fee             = int(req['maxFee']),
        validUntil      = req['validUntil']
    )

    # print(f"PoolExit type hash = {bytes.hex(exit.type_hash())}")
    return EIP712.hash_packed(
        EIP712.ammPoolDomains[req['poolAddress']].hash_struct(),
        exit.hash_struct()
    )

import sys

if __name__ == "__main__":
    EIP712.init_amm_env(name=sys.argv[2],
                version="1.0.0",
                chainId=sys.argv[1],
                verifyingContract=sys.argv[3])
    domainSep = EIP712.ammPoolDomains[sys.argv[3]].hash_struct()
    print("0x" + bytes.hex(domainSep).zfill(64))