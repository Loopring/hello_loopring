# hello_loopring

This repository contains examples of using the Loopring Relayer APIs to interact with Loopring Exchange (https://loopring.io).

## Requirement

1. Before running, set `PYTHONPATH`to project's root directory first, so it refers to local ethsnarks projects.
2. Run `pip install -r requirements.txt` to install dependencies.

## Hash and Sign

Hash and Sign provides python sample code to show how loopring hash and sign inputs, as below:

```bash
$ python hash_and_sign/poseidon_hash_sample.py -h
usage: poseidon_hash_sample.py [-h] -a {hash,sign} [-i INPUTS] [-k PRIVATEKEY]

Loopring Hash and Sign Code Sample

optional arguments:
  -h, --help            show this help message and exit
  -a {hash,sign}, --action {hash,sign}
                        choose action, "hash" calculates poseidon hash of
                        inputs. "sign" signs the message.
  -i INPUTS, --inputs INPUTS
                        hash or sign message inputs. For poseidon hash, they
                        should be number string list separated by "," like
                        “1,2,3,4,5,6”, max len is 13 to compatible with
                        loopring DEX config
  -k PRIVATEKEY, --privatekey PRIVATEKEY
                        private key to sign the inputs, should be a big int
                        string, like “12345678”, user can try the key exported
                        from loopring DEX

```

### Hash Inputs

Action `hash` calculates `PoseidonHash` of the inputs, the inputs should be a integer list string separated by `','`, as below, output of hash is still a integer string.

```bash
$ python hash_and_sign/poseidon_hash_sample.py -a hash -i "1,2,3,4,5,6"
poseidon_hash [1, 2, 3, 4, 5, 6]
hash of [1, 2, 3, 4, 5, 6] is 6176773444289981846118307839281474150806945949724611589346553109129622523596
```

### Sign Inputs

Action `sign` signs the inputs by using user's `privatekey`, the output is the `EDDSA` signature of the inputs which include `Rx`,`Ry`,and `S` according to `EDDSA`'s specification. In loopringDEX, we concatenate these 3 parts together, as below.

```bash
$ python hash_and_sign/poseidon_hash_sample.py -a sign -i "1,2,3,4,5,6" -k "123456"
loopring sign message 1,2,3,4,5,6
signature of '1,2,3,4,5,6' is 13467847531487527001260274356653369902629934602648792938137682849997702052810,17034102387132086143868408284736328722663534859319845015635221999547971712812,15235585622868842803104165188060147849906727947244637197326176093821390010072
```

## Trading Example

Trading sample provides sample code to place/cancel order, which involves all loopring specific operations include hash, sign, orderId management, etc. Sample code is written by python, and its main entry is `trading/trading_sample.py`.

```bash
$ python trading/trading_example.py -h
usage: trading_example.py [-h] -a {time,buy,sell,cancel} [-m MARKET] [-p PRICE]
                         [-v VOLUME] [-O ORDERID] [-H ORDERHASH]

LoopringRestSample

optional arguments:
  -h, --help            show this help message and exit
  -a {time,buy,sell,cancel}, --action {time,buy,sell,cancel}
                        choose action
  -m MARKET, --market MARKET
                        specific token market
  -p PRICE, --price PRICE
                        order price
  -v VOLUME, --volume VOLUME
                        order volume
  -O ORDERID, --Orderid ORDERID
                        order id
  -H ORDERHASH, --orderHash ORDERHASH
                        order hash
```

The only things users need to do is config their account in trading_sample.py using information exported from [loopring DEX](<https://loopring.io/trade/>), as below:

```python
loopring_exported_account = {
    "exchangeName"    : "LoopringDEX: Beta 1",
    "exchangeAddress" : "0x944644Ea989Ec64c2Ab9eF341D383cEf586A5777",
    "exchangeId"      : 2,
    "accountAddress"  : "USER'S account address",
    "accountId"       : 1234,
    "apiKey"          : "USER'S api key",
    "publicKeyX"      : "USER's publicKeyX",
    "publicKeyY"      : "USER's publicKeyY",
    "privateKey"      : "USER's privateKey"
}
```

### Check Environment

```bash
$ python trading/trading_example.py -a time
on_query_time: {'resultInfo': {'code': 0, 'message': 'SUCCESS'}, 'data': 1586596797476}
```

### Place Order

```bash
$ python trading/trading_example.py -a buy -p 0.01 -v 1000 -m "LRC-USDT"
place order success: hash=4963352290219542297406476799052752911203044270145934664174347699420370758697, clientOrderId=SampleOrder1586598415
```

### Cancel Order

```bash
$ python trading/trading_example.py -a cancel -O SampleOrder1586598415
cancel_order SampleOrder1586596856
on_cancel_order {'resultInfo': {'code': 0, 'message': 'SUCCESS'}, 'data': True} {'accountId': 1234, 'clientOrderId': 'SampleOrder1586598415'}
cancel order success

```

