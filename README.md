# Hello Loopring

 Loopring V3 api sample with sdk

## Install

```bash
    $pip install -r requirements.txt    # install lib dependencies
    $export PYTHONPATH=${PWD}           # use local ethsnarks to avoid conflicts
```

## Directory Contents

```she
.
├── sdk: sdk utils, include poseidon hash, both ecdsa/eddsa signing and a workable loopringV3 sample client with full Loopring L2 functions.
├── test: ecdsa & eddsa signing tests, as helper to debug signature issues.
├── tutorials: hash/signing code example, and a step-by-step tutorial of loopring transfer.
└── v3explorer: client sample with full DEX functions.
```

## Getting Started

Use tutorials to get familiar with how to do sign a request, and how to make a L2 offchain request in Loopring DEX. Go to [Tutorial](https://github.com/Loopring/hello_loopring/tree/loopring-v3/tutorials) for more details

## A Full Function Client 

There is a full function client sample in v3explorer, user can test all L2 requests by that. Refer to [V3explorer](https://github.com/Loopring/hello_loopring/tree/loopring-v3/v3explorer) directory for more details.

## Contacts

- [exchange@loopring.io](mailto:exchange@loopring.io)
- [Loopring Discord](https://discord.gg/KkYccYp)

