import argparse
import sys
from trading.loopring_rest_sample import LoopringRestApiSample
from time import sleep

loopring_exported_account =     {
    "name" : "",
    "exchangeName": "LoopringDEX: Beta 1",
    "exchangeAddress": "0x944644Ea989Ec64c2Ab9eF341D383cEf586A5777",
    "exchangeId": 2,
    "accountAddress": "",
    "accountId": 0,
    "apiKey": "",
    "publicKeyX": "",
    "publicKeyY": "",
    "privateKey": ""
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loopring DEX Rest API Trading Example")
    parser.add_argument("-a", "--action", required=True,
                        choices=['time', 'buy', 'batch_buy', 'sell', 'batch_sell', 'cancel'], default='time', help='choose action')
    parser.add_argument("-m", "--market", default="LRC-USDT", help='specific token market')
    parser.add_argument("-p", "--price", help='order price or prices(, splited prices) if batch mode')
    parser.add_argument("-v", "--volume", help='order volume or volumes(, splited volumes) if batch mode')
    parser.add_argument("-O", "--orderid", help='order id to be cancelled')
    parser.add_argument("-H", "--orderhash", help='order hash to be cancelled')

    args = parser.parse_args()

    loopring_rest_sample = LoopringRestApiSample()
    if args.action == "time":
        srv_time = loopring_rest_sample.query_srv_time()
        print(f"srv time is {srv_time}")
    else:
        loopring_rest_sample.connect(loopring_exported_account)
        if args.action == "buy":
            buy_token, sell_token = args.market.split('-')
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.buy(buy_token, sell_token, price, volume)
        if args.action == "batch_buy":
            buy_token, sell_token = args.market.split('-')
            prices =  [float(p) for p in args.price.split(',')]
            volumes = [float(v) for v in args.volume.split(',')]
            loopring_rest_sample.batch_buy(buy_token, sell_token, prices, volumes)
        elif args.action == "sell":
            buy_token, sell_token = args.market.split('-')
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.sell(buy_token, sell_token, price, volume)
        elif args.action == "batch_sell":
            buy_token, sell_token = args.market.split('-')
            prices =  [float(p) for p in args.price.split(',')]
            volumes = [float(v) for v in args.volume.split(',')]
            loopring_rest_sample.batch_sell(buy_token, sell_token, prices, volumes)
        elif args.action == "cancel":
            cancal_params = {}
            if args.orderhash:
                cancal_params['orderHash'] = args.orderhash
            if args.orderid:
                cancal_params['clientOrderId'] = args.orderid
            loopring_rest_sample.cancel_orders(**cancal_params)
        sleep(5)
