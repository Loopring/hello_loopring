import argparse
from decimal import Decimal
import sys
from time import sleep

from sdk.ethsnarks.eddsa import PoseidonEdDSA
from sdk.loopring_v3_client import LoopringV3Client


loopring_exported_account = {
    "name" : "UAT Account 1",
    "chainId": 5,
    "exchangeName": "LoopringDEX: V2",
    "exchangeAddress": "0x12b7cccF30ba360e5041C6Ce239C9a188B709b2B",
    "accountAddress": "0x727e0fa09389156fc803eaf9c7017338efd76e7f",
    "accountId": 10037,
    "apiKey": "JC1vbpMLprvoALsNFuhyCkVsTwZa2TSyMsP9fW1jLhR6yMbWcygnrcxcfHNnnRHk",
    "publicKeyX": "0x1959921f5f8d4f486b4c57afd6459444be34c75eede50ff1bd00b0333887eb70",
    "publicKeyY": "0x2bb25e133b1294626e1154e662b38d9332b66927451813c1615912fd705b7720",
    "privateKey": "0x5db65ed466a3b154dcf83e2e4b06b66c0c305d7d2088f9f60031567cf080dc1",
    "ecdsaKey"  : "491aecdb1d5f6400a6b62fd12a41a86715bbab675c37a4060ba115fecf94083c",
    "whitelisted": False
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loopring DEX Rest API 3.6 Trading Example")
    parser.add_argument("-a", "--action", required=True,
                        choices=[
                            'time', 'apiKey',
                            #order
                            'buy', 'sell', 'cancel',
                            #offchain requests
                            'transfer', 'withdraw', 'update',
                            #amm
                            'join', 'exit', 'swap-buy', 'swap-sell',
                            #misc
                            'report', 'query',
                            #on-chain op
                            'deposit'
                            ],
                            default='time', help='choose action')
    parser.add_argument("-m", "--market", default="LRC-USDT", help='specific token market')
    parser.add_argument("-n", "--poolName", default="LRC-USDT", help='specific AMM pool name')
    parser.add_argument("-d", "--direction", default="0", help='direction of swap')
    parser.add_argument("-t", "--token", default="LRC", help='specific token to transfer')
    parser.add_argument("-k", "--key", default="0x4a3d1e098350", help='specific eddsa key tobe updated')
    parser.add_argument("-u", "--user_to", default="", help='specific user_to account address to transfer')
    parser.add_argument("-p", "--price", help='order price or prices(, splited prices) if batch mode')
    parser.add_argument("-v", "--volume", help='order volume or volumes(, splited volumes) if batch mode')
    parser.add_argument("-b", "--burnOrmint", help='token to be burn/mint')
    parser.add_argument("-O", "--orderid", help='order id to be cancelled')
    parser.add_argument("-H", "--orderhash", help='order hash to be cancelled')
    parser.add_argument("-T", "--queryType", help='operation type to be approved')

    args = parser.parse_args()

    loopring_rest_sample = LoopringV3Client()
    if args.action == "time":
        srv_time = loopring_rest_sample.query_srv_time()
        print(f"srv time is {srv_time}")
    else:
        loopring_rest_sample.connect(loopring_exported_account)
        if args.action == "buy":
            buy_token, sell_token = args.market.split('-')
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.send_order(buy_token, sell_token, True, price, volume)
        elif args.action == "sell":
            buy_token, sell_token = args.market.split('-')
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.send_order(buy_token, sell_token, False, price, volume)
        elif args.action == "cancel":
            cancal_params = {}
            if args.orderhash:
                cancal_params['orderHash'] = args.orderhash
            elif args.orderid:
                cancal_params['clientOrderId'] = args.orderid
            loopring_rest_sample.cancel_order(**cancal_params)
        if args.action == "transfer":
            token = args.token
            to = args.user_to
            amount = Decimal(args.volume)
            loopring_rest_sample.transfer_eddsa(to, token, amount)
        elif args.action == "withdraw":
            token = args.token
            to = args.user_to if args.user_to != "" else args.user_to
            amount = Decimal(args.volume)
            loopring_rest_sample.offchainWithdraw_eddsa(to, token, amount, 0, bytes(0))
        elif args.action == "update":
            privkey = int(args.key, 16)
            pubKey = PoseidonEdDSA.B() * privkey
            # print(pubKey)
            loopring_rest_sample.update_account_eddsa(privkey, pubKey)
        elif args.action == 'join':
            joinAmounts = [Decimal(v) for v in args.volume.split(',')]
            mint = Decimal(args.burnOrmint)
            poolName = args.market
            poolAddr = loopring_rest_sample.ammPoolNames[poolName]
            loopring_rest_sample.join_amm_pool(poolName, joinAmounts, mint)
        elif args.action == 'exit':
            exitAmounts = [Decimal(v) for v in args.volume.split(',')]
            burn = Decimal(args.burnOrmint)
            token = args.token
            poolName = args.market
            poolAddr = loopring_rest_sample.ammPoolNames[poolName]
            loopring_rest_sample.exit_amm_pool(poolName, burn, exitAmounts)
        elif args.action == 'swap-buy':
            buy_token, sell_token = args.market.split('-')
            poolName = args.poolName
            poolAddr = loopring_rest_sample.ammPoolNames[poolName]
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.send_order(buy_token, sell_token, True, price, volume, poolAddr)
        elif args.action == 'swap-sell':
            buy_token, sell_token = args.market.split('-')
            poolName = args.poolName
            poolAddr = loopring_rest_sample.ammPoolNames[poolName]
            price =  float(args.price)
            volume = float(args.volume)
            loopring_rest_sample.send_order(buy_token, sell_token, False, price, volume, poolAddr)
        elif args.action == 'report':
            loopring_rest_sample.get_account()
            loopring_rest_sample.get_apiKey()
            loopring_rest_sample.query_balance()
        elif args.action == 'query':
            # hash = args.orderhash
            if args.queryType == 'orders':
                loopring_rest_sample.get_orders()
            elif args.queryType == 'transfers':
                loopring_rest_sample.get_transfers()
            elif args.queryType == 'trades':
                loopring_rest_sample.get_trades()
            elif args.queryType == 'withdrawals':
                loopring_rest_sample.get_withdrawals()
            elif args.queryType in ['join', 'exit', 'amm']:
                loopring_rest_sample.get_amm_txs()
            elif args.queryType == 'pools':
                loopring_rest_sample.query_info("amm/pools")
            elif args.queryType == 'markets':
                loopring_rest_sample.query_info("exchange/info")
        sleep(5)
