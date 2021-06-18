import hashlib
import sys

from sdk.ethsnarks.eddsa import PureEdDSA, PoseidonEdDSA
from sdk.ethsnarks.field import FQ, SNARK_SCALAR_FIELD
from sdk.ethsnarks.poseidon import poseidon_params, poseidon
from sdk.sig_utils.eddsa_utils import *
import argparse

MAX_INPUT = 13

class TutorialEddsaSignHelper(EddsaSignHelper):
    def __init__(self, private_key="0x1"):
        super(TutorialEddsaSignHelper, self).__init__(
            poseidon_params = poseidon_params(SNARK_SCALAR_FIELD, MAX_INPUT + 1, 6, 53, b'poseidon', 5, security_target=128),
            private_key = private_key
        )

    def serialize_data(self, inputs):
        return [int(data) for data in inputs][:MAX_INPUT]

def loopring_poseidon_hash(inputs):
    # prepare params, using loopring order params
    print(f"poseidon_hash {inputs}")
    hasher = TutorialEddsaSignHelper()
    hash_value = hasher.hash(inputs)
    return hash_value

def loopring_sign(input_message, private_key):
    print(f"loopring sign message {input_message}")
    hasher = TutorialEddsaSignHelper(private_key)
    signature = hasher.sign(inputs)
    return signature

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loopring Hash and Sign Code Sample")
    parser.add_argument("-a", "--action", required=True, choices=['hash', 'sign'], help='choose action, "hash" calculates poseidon hash of inputs. "sign" signs the message.')
    parser.add_argument("-i", "--inputs", help='hash or sign message inputs. For poseidon hash, they should be number string list separated by "," like “1,2,3,4,5,6”, max len is 13 to compatible with loopring DEX config')
    parser.add_argument("-k", "--privatekey", default=None, help='private key to sign the inputs, should be a big int string, like “12345678”, user can try the key exported from loopring DEX')

    args = parser.parse_args()

    if args.action == "sign":
        inputs = [int(i) for i in args.inputs.split(',')]
        private_key = args.privatekey
        assert private_key is not None and private_key[:2] == '0x'
        sign = loopring_sign(inputs, private_key)
        print(f"signature of '{inputs}' is {sign}")
    elif args.action == "hash":
        inputs = [int(i) for i in args.inputs.split(',')]
        assert len(inputs) <= MAX_INPUT
        hash_value = loopring_poseidon_hash(inputs)
        print(f"hash of {inputs} is {hash_value}")
