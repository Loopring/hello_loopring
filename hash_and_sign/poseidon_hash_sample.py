import hashlib
import sys

from ethsnarks.eddsa import PureEdDSA, PoseidonEdDSA
from ethsnarks.field import FQ, SNARK_SCALAR_FIELD
from ethsnarks.poseidon import poseidon_params, poseidon
import argparse


MAX_INPUT = 13

def loopring_poseidon_hash(inputs):
    # prepare params, using loopring order params
    print(f"poseidon_hash {inputs}")
    params = poseidon_params(SNARK_SCALAR_FIELD, MAX_INPUT + 1, 6, 53, b'poseidon', 5, security_target=128)
    hash_value = poseidon(inputs, params)
    return hash_value

def loopring_sign(input_message, private_key):
    print(f"loopring sign message {input_message}")
    hasher = hashlib.sha256()
    hasher.update(input_message.encode('utf-8'))
    msgHash = int(hasher.hexdigest(), 16) % SNARK_SCALAR_FIELD
    signed = PoseidonEdDSA.sign(msgHash, FQ(int(private_key)))
    signature = ','.join(str(_) for _ in [signed.sig.R.x, signed.sig.R.y, signed.sig.s])
    return signature


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loopring Hash and Sign Code Sample")
    parser.add_argument("-a", "--action", required=True, choices=['hash', 'sign'], help='choose action, "hash" calculates poseidon hash of inputs. "sign" signs the message.')
    parser.add_argument("-i", "--inputs", help='hash or sign message inputs. For poseidon hash, they should be number string list separated by "," like “1,2,3,4,5,6”, max len is 13 to compatible with loopring DEX config')
    parser.add_argument("-k", "--privatekey", default=None, help='private key to sign the inputs, should be a big int string, like “12345678”, user can try the key exported from loopring DEX')

    args = parser.parse_args()

    if args.action == "sign":
        inputs = args.inputs
        private_key = args.privatekey
        assert private_key is not None
        sign = loopring_sign(inputs, private_key)
        print(f"signature of '{inputs}' is {sign}")
    elif args.action == "hash":
        inputs = [int(i) for i in args.inputs.split(',')]
        assert len(inputs) <= MAX_INPUT
        hash_value = loopring_poseidon_hash(inputs)
        print(f"hash of {inputs} is {hash_value}")
