# Loopring V3 api sample.

## install

```bash
    $pip install -r requirements.txt    # install lib dependencies
    $export PYTHONPATH=${PWD}           # use local ethsnarks
```

## command line usage

### setup account
Set config got from [Loopring UAT Env](https://loopring-amm.herokuapp.com/)
```python
    loopring_exported_account = {
        "name" : "DEV Account 1",
        "exchangeName": "LoopringDEX: V2",
        "exchange": "",
        "address": "",
        "accountId": 1,
        "apiKey": "",
        "chainId": 5,
        "publicKeyX": "",
        "publicKeyY": "",
        "ecdsaKey": "",
        "eddsaKey": ""
    }
```

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
    $python v3explorer/api_explorer.py -a swap-buy -m LRC-ETH -p 0.9 -v 100
    $python v3explorer/api_explorer.py -a swap-sell -m LRC-ETH -p 1.0 -v 100
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