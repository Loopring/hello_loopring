# Loopring V3 api sample.

## install

```bash
    $pip install -r requirements.txt    # install lib dependencies
    $export PYTHONPATH=${PWD}           # use local ethsnarks
```

## command line usage

### setup account
Set config got from [Loopring UAT Env](https://loopring-amm.herokuapp.com/), the exported value is like this:
```python
    loopring_exported_account = {
      "name" : "DEV Account 1",
      "exchangeName": "LoopringDEX: V2",
      "exchangeAddress": "0x2e76EBd1c7c0C8e7c2B875b6d505a260C525d25e",
      "chainId": 5,
      "accountAddress": "0x2c87779572103fFD97CbF0BFAe26Ce7a73Bbec6f",
      "accountId": 10000,
      "apiKey": "J7SXWMiASnJADr4awM2SzhycLPxqxPF992nDylMs7KzNcb3BAUY3HOtQV2bWQGR0",
      "publicKeyX": "0x02e600476845fcfd95a72ad267d469db98db065f4ba642ee1d99d7e7f4d37d54",
      "publicKeyY": "0x06bc5ab7c06b777dcadaee66fadd6cef8c6010e3fb6927df88acecf5d8b006a1",
      "privateKey": "0x4f047d81732cdb4b6ef00117a57cb9bff167c20bb17e1d375947db4aa561ee9",
      # extra settings
      "ecdsaKey"  : "0x1",
      "whitelisted": False
    }
```
There are 2 extra settings. ecdsaKey is for L1 account ownership authentication, directly move L2 token operations like transfer & withdraw need extra L1 signatures. However, if you are a professional user, you can register to Loopring's whitelist to skip this step, which makes transfer especially payment convenient & fast.

### update passowrd

```bash
    $python v3explorer/api_explorer.py -a update -k 0x4c388978a9cd17ff7171fb8694fb7618c8bf48e7c800e81277870c6bf12e47b
```

### transfer

```bash
    $python v3explorer/api_explorer.py -a transfer -t LRC -v 100 -u 0xd854872f17c2783ae9d89e7b2a29cd72ec2a74ff
```

### withdraw

```bash
    $python v3explorer/api_explorer.py -a withdraw -t LRC -v 5000
```

### order

```bash
    $python v3explorer/api_explorer.py -a sell -m LRC-ETH -p 1 -v 100
    $python v3explorer/api_explorer.py -a buy -m LRC-ETH -p 0.9 -v 100
```

### swap

```bash
    $python v3explorer/api_explorer.py -a swap-sell -n LRCETH-Pool -m LRC-ETH -p 1.0 -v 100
    $python v3explorer/api_explorer.py -a swap-buy -n LRCETH-Pool -m LRC-ETH -p 0.9 -v 100
```

### report account
```bash
    $python v3explorer/api_explorer.py -a report
```

### query account logs
```bash
    $python v3explorer/api_explorer.py -a query -T transfers
    $python v3explorer/api_explorer.py -a query -T orders
    $python v3explorer/api_explorer.py -a query -T amm
    ...
```