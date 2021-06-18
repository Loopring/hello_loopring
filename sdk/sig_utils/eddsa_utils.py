from sdk.ethsnarks.eddsa import PureEdDSA, PoseidonEdDSA
from sdk.ethsnarks.field import FQ, SNARK_SCALAR_FIELD
from sdk.ethsnarks.poseidon import poseidon_params, poseidon
from sdk.ethsnarks.eddsa import Signature, SignedMessage
import urllib
import hashlib

class EddsaSignHelper:
    def __init__(self, poseidon_params, private_key = "0x1"):
        self.poseidon_sign_param = poseidon_params
        self.private_key = FQ(int(private_key, 16))
        assert self.private_key != FQ.zero()
        # print(f"self.private_key = {self.private_key}")

    def hash(self, structure_data):
        serialized_data = self.serialize_data(structure_data)
        msgHash = poseidon(serialized_data, self.poseidon_sign_param)
        return msgHash

    def sign(self, structure_data):
        msgHash = self.hash(structure_data)
        signedMessage = PoseidonEdDSA.sign(msgHash, self.private_key)
        return "0x" + "".join([
                        hex(int(signedMessage.sig.R.x))[2:].zfill(64),
                        hex(int(signedMessage.sig.R.y))[2:].zfill(64),
                        hex(int(signedMessage.sig.s))[2:].zfill(64)
                    ])
    
    def sigStrToSignature(self, sig):
        assert len(sig) == 194
        pureHexSig = sig[2:]
        return Signature(
            [
                int(pureHexSig[:64], 16),
                int(pureHexSig[64:128], 16)
            ],
            int(pureHexSig[128:], 16)
        )

    def serialize_data(self, data):
        pass

    def verify(self, message, sig):
        return PoseidonEdDSA.verify(sig.A, sig.sig, sig.msg)

class DummyEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(DummyEddsaSignHelper, self).__init__(
            poseidon_params = poseidon_params(SNARK_SCALAR_FIELD, 2, 6, 53, b'poseidon', 5, security_target=128),
            private_key = private_key
        )

    def serialize_data(self, dummy):
        return [
            int(dummy["data"]),
        ]

class UrlEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key, host=""):
        self.host = host
        super(UrlEddsaSignHelper, self).__init__(
            poseidon_params = poseidon_params(SNARK_SCALAR_FIELD, 2, 6, 53, b'poseidon', 5, security_target=128),
            private_key = private_key
        )
    
    def hash(self, structure_data):
        serialized_data = self.serialize_data(structure_data)
        hasher = hashlib.sha256()
        hasher.update(serialized_data.encode('utf-8'))
        msgHash = int(hasher.hexdigest(), 16) % SNARK_SCALAR_FIELD
        return msgHash

    def serialize_data(self, request):
        method = request.method
        url = urllib.parse.quote(self.host + request.path, safe='')
        data = urllib.parse.quote("&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in request.params.items()]), safe='')
        # return "&".join([method, url.replace("http", "https"), data])
        return "&".join([method, url, data])

class OrderEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(OrderEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 12, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )
    
    def serialize_data(self, order):
        return [
            int(order["exchange"], 16),
            int(order["storageId"]),
            int(order["accountId"]),
            int(order["sellToken"]['tokenId']),
            int(order["buyToken"]['tokenId']),
            int(order["sellToken"]['volume']),
            int(order["buyToken"]['volume']),
            int(order["validUntil"]),
            int(order["maxFeeBips"]),
            int(order["fillAmountBOrS"]),
            int(order.get("taker", "0x0"), 16)
        ]

class UpdateAccountEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(UpdateAccountEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 9, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )
    
    def serialize_data(self, updateAccount):
        return [
            int(updateAccount['exchange'], 16),
            int(updateAccount['accountId']),
            int(updateAccount['maxFee']['tokenId']),
            int(updateAccount['maxFee']['volume']),
            int(updateAccount['publicKey']['x'], 16),
            int(updateAccount['publicKey']['y'], 16),
            int(updateAccount['validUntil']),
            int(updateAccount['nonce'])
        ]

class OriginTransferEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(OriginTransferEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 13, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )

    def serialize_data(self, originTransfer):
        return [
            int(originTransfer['exchange'], 16),
            int(originTransfer['payerId']),
            int(originTransfer['payeeId']), # payer_toAccountID
            int(originTransfer['token']['tokenId']),
            int(originTransfer['token']['volume']),
            int(originTransfer['maxFee']['tokenId']),
            int(originTransfer['maxFee']['volume']),
            int(originTransfer['payeeAddr'], 16), # payer_to
            0, #int(originTransfer.get('dualAuthKeyX', '0'),16),
            0, #int(originTransfer.get('dualAuthKeyY', '0'),16),
            int(originTransfer['validUntil']),
            int(originTransfer['storageId'])
        ]

class DualAuthTransferEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(DualAuthTransferEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 13, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )

    def serialize_data(self, dualAuthTransfer):
        return [
            int(dualAuthTransfer['exchange'],16),
            int(dualAuthTransfer['accountId']),
            int(dualAuthTransfer['payee_toAccountID']),
            int(dualAuthTransfer['token']),
            int(dualAuthTransfer['amount']),
            int(dualAuthTransfer['feeToken']),
            int(dualAuthTransfer['maxFeeAmount']),
            int(dualAuthTransfer['to'],16),
            int(dualAuthTransfer.get('dualAuthKeyX', '0'),16),
            int(dualAuthTransfer.get('dualAuthKeyY', '0'),16),
            int(dualAuthTransfer['validUntil']),
            int(dualAuthTransfer['storageId']),
        ]

class WithdrawalEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(WithdrawalEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 10, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )

    def serialize_data(self, withdraw):
        return [
            int(withdraw['exchange'], 16),
            int(withdraw['accountId']),
            int(withdraw['token']['tokenId']),
            int(withdraw['token']['volume']),
            int(withdraw['maxFee']['tokenId']),
            int(withdraw['maxFee']['volume']),
            int(withdraw['onChainDataHash'], 16),
            int(withdraw['validUntil']),
            int(withdraw['storageId']),
        ]

class MessageHashEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(MessageHashEddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 2, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )

    def hash(self, eip712_hash_bytes):
        return self.serialize_data(eip712_hash_bytes)

    def serialize_data(self, data):
        if isinstance(data, bytes):
            return int(data.hex(), 16) >> 3
        elif isinstance(data, str):
            return int(data, 16) >> 3
        else:
            raise TypeError("Unknown type " + str(type(data)))

class MessageHash2EddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key):
        super(MessageHash2EddsaSignHelper, self).__init__(
            poseidon_params(SNARK_SCALAR_FIELD, 2, 6, 53, b'poseidon', 5, security_target=128),
            private_key
        )

    def hash(self, eip712_hash_bytes):
        return self.serialize_data(eip712_hash_bytes)

    def serialize_data(self, data):
        if isinstance(data, bytes):
            return int(data.hex(), 16)  % SNARK_SCALAR_FIELD
        elif isinstance(data, str):
            return int(data, 16)  % SNARK_SCALAR_FIELD
        else:
            raise TypeError("Unknown type " + str(type(data)))