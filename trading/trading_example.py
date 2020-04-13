import argparse
import sys
from trading.loopring_rest_sample import LoopringRestApiSample
from time import sleep

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loopring DEX Rest API Trading Example")
    parser.add_argument("-a", "--action", required=True, choices=['time', 'buy', 'sell', 'cancel'], default='time', help='choose action')
    parser.add_argument("-m", "--market", default="LRC-USDT", help='specific token market')
    parser.add_argument("-p", "--price", help='order price')
    parser.add_argument("-v", "--volume", help='order volume')
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
        elif args.action == "sell":
            buy_token, sell_token = args.market.split('-')
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.sell(buy_token, sell_token, price, volume)
        elif args.action == "cancel":
            cancal_params = {}
            if args.orderhash:
                cancal_params['orderHash'] = args.orderhash
            if args.orderid:
                cancal_params['clientOrderId'] = args.orderid
            loopring_rest_sample.cancel_order(**cancal_params)
        sleep(5)
