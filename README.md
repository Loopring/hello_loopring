# hello_loopring

This repository contains examples of using the Loopring Relayer APIs to interact with Loopring Exchange (https://loopring.io).

## Trading Sample

Trading sample provides sample code to place/cancel order, which involves all loopring specific operations include hash, sign, orderId management, etc. Sample code is written by python, and its main entry is `trading/trading_sample.py`, before running, set `PYTHONPATH`to project's root directory first.

```bash
$ python trading/trading_sample.py -h
usage: trading_sample.py [-h] -a {time,buy,sell,cancel} [-m MARKET] [-p PRICE]
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
                        cancel order id
  -H ORDERHASH, --orderHash ORDERHASH
                        cancel order hash
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
$ python trading/trading_sample.py -a time
on_query_time: {'resultInfo': {'code': 0, 'message': 'SUCCESS'}, 'data': 1586596797476}
```

### Place Order

```bash
$ python trading/trading_sample.py -a buy -p 0.01 -v 1000 -m "LRC-USDT"
place order success: hash=4963352290219542297406476799052752911203044270145934664174347699420370758697, clientOrderId=SampleOrder1586598415
```

###Cancel Order

```bash
$ python trading/trading_sample.py -a cancel -O SampleOrder1586598415
cancel_order SampleOrder1586596856
on_cancel_order {'resultInfo': {'code': 0, 'message': 'SUCCESS'}, 'data': True} {'accountId': 1234, 'clientOrderId': 'SampleOrder1586598415'}
cancel order success

```

