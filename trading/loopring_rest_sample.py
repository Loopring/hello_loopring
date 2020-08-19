"""
REST API Sample for Loopring Crypto Exchange.
"""
import hashlib
import hmac
import json
from copy import copy
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from operator import itemgetter
from random import randint
import re
import sys
from time import time, sleep
import urllib

from trading.rest_client import RestClient, Request
from ethsnarks.eddsa import PureEdDSA, PoseidonEdDSA
from ethsnarks.field import FQ, SNARK_SCALAR_FIELD
from ethsnarks.poseidon import poseidon_params, poseidon


class Security(Enum):
    NONE = 0
    SIGNED = 1
    API_KEY = 2

class LoopringRestApiSample(RestClient):
    """
    LOOPRING REST API SAMPLE
    """

    LOOPRING_REST_HOST   = "https://api.loopring.io"
    MAX_ORDER_ID = 1_000_000

    market_info_map = {
        "ETH"  : {"tokenId":0, "symbol":"ETH",  "decimals":18},
        "LRC"  : {"tokenId":2, "symbol":"LRC",  "decimals":18},
        "USDT" : {"tokenId":3, "symbol":"USDT", "decimals":6},
        "DAI"  : {"tokenId":5,"symbol":"DAI","decimals":18}
    }

    def __init__(self):
        """"""
        super().__init__()
        # exported account
        self.api_key     = ""
        self.private_key = ""
        self.address     = ""
        self.publicKeyX  = ""
        self.publicKeyY  = ""
        self.accountId   = 0
        self.batch_size  = 2
        assert self.batch_size <= 10

        # order related
        self.orderId     = [None] * 256
        self.time_offset = 0
        self.order_sign_param = poseidon_params(SNARK_SCALAR_FIELD, 14, 6, 53, b'poseidon', 5, security_target=128)

        self.init(self.LOOPRING_REST_HOST)
        self.start()

    def connect(self, exported_secret : dict):
        """
        Initialize connection to LOOPRING REST server.
        """
        self.api_key     = exported_secret['apiKey']
        self.exchangeId  = exported_secret['exchangeId']
        self.private_key = exported_secret['privateKey'].encode()
        self.address     = exported_secret['accountAddress']
        self.accountId   = exported_secret['accountId']

        # align srv and local time
        self.query_time()
        for token_id in [info['tokenId'] for info in self.market_info_map.values()]:
            self.query_orderId(token_id)
        sleep(8)

    def sign(self, request):
        """
        Generate LOOPRING signature.
        """
        security = request.data.pop("security", Security.NONE)
        if security == Security.NONE:
            if request.method == "POST":
                request.data = request.params
                request.params = {}
            return request

        if request.params:
            path = request.path + "?" + urllib.parse.urlencode(request.params)
        else:
            request.params = dict()
            path = request.path

        # request headers
        headers = {
            "Content-Type" : "application/x-www-form-urlencoded",
            "Accept"       : "application/json",
            "X-API-KEY"    : self.api_key,
        }
        if request.headers != None:
            headers.update(request.headers)

        if security == Security.SIGNED:
            ordered_data = self._encode_request(request)
            hasher = hashlib.sha256()
            hasher.update(ordered_data.encode('utf-8'))
            msgHash = int(hasher.hexdigest(), 16) % SNARK_SCALAR_FIELD
            signed = PoseidonEdDSA.sign(msgHash, FQ(int(self.private_key)))
            signature = ','.join(str(_) for _ in [signed.sig.R.x, signed.sig.R.y, signed.sig.s])
            headers.update({"X-API-SIG": signature})

        request.path = path
        if request.method != "GET":
            request.data = json.dumps(request.data) if len(request.data) != 0 else request.params
            request.params = {}
        else:
            request.data = {}

        request.headers = headers

        # print(f"finish sign {request}")
        return request

    def _encode_request(self, request):
        method = request.method
        url = urllib.parse.quote(self.LOOPRING_REST_HOST + request.path, safe='')
        data = urllib.parse.quote("&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in request.params.items()]), safe='')
        return "&".join([method, url, data])

    def query_srv_time(self):
        data = {
            "security": Security.NONE
        }

        response = self.request(
            "GET",
            path="/api/v2/timestamp",
            data=data
        )
        json_resp = response.json()
        if json_resp['resultInfo']['code'] != 0:
            raise AttributeError(f"on_query_time failed {data}")
        return json_resp['data']

    def query_time(self):
        """"""
        data = {
            "security": Security.NONE
        }

        self.add_request(
            "GET",
            path="/api/v2/timestamp",
            callback=self.on_query_time,
            data=data
        )

    def on_query_time(self, data, request):
        if data['resultInfo']['code'] != 0:
            raise AttributeError(f"on_query_time failed {data}")
        local_time = int(time() * 1000)
        server_time = int(data["data"])
        self.time_offset = int((local_time - server_time) / 1000)

    def query_orderId(self, tokenId):
        """"""
        data = {
            "security": Security.API_KEY
        }
        params = {
            "accountId": self.accountId,
            "tokenSId": tokenId
        }
        self.add_request(
            method="GET",
            path="/api/v2/orderId",
            callback=self.on_query_orderId,
            params=params,
            data=data
        )

    def on_query_orderId(self, data, request):
        # print(f"on_query_orderId {request} {data}")
        if data['resultInfo']['code'] != 0:
            raise AttributeError(f"on_query_orderId failed {data}")

        tokenId = request.params['tokenSId']
        self.orderId[tokenId] = int(data['data'])

    def buy(self, base_token, quote_token, price, volume):
        """
        Place buy order
        """
        self._order(base_token, quote_token, True, price, volume)

    def sell(self, base_token, quote_token, price, volume):
        """
        Place sell order
        """
        self._order(base_token, quote_token, False, price, volume)

    def _order(self, base_token, quote_token, buy, price, volume):
        order = self._create_order(base_token, quote_token, buy, price, volume)
        # print(f"create new order {order}")
        data = {"security": Security.API_KEY}
        headers = {
            "Content-Type": "application/json",
        }

        self.add_request(
            method="POST",
            path="/api/v2/order",
            callback=self.on_send_order,
            params=order,
            data=data,
            extra=order
        )

    def batch_buy(self, base_token, quote_token, prices, volumes):
        """
        Place batch buy order
        """
        self.batch_orders(base_token, quote_token, True, prices, volumes)

    def batch_sell(self, base_token, quote_token, prices, volumes):
        """
        Place batch sell order
        """
        self.batch_orders(base_token, quote_token, False, prices, volumes)

    def batch_orders(self, base_token, quote_token, is_buy, prices, volumes):
        """
        Place sell order
        """
        assert(len(prices) == len(volumes))
        i = 0
        batch_size = self.batch_size
        while i*batch_size < len(prices):
            batch_prices  =  prices[i*batch_size : (i+1)*batch_size]
            batch_volumes = volumes[i*batch_size : (i+1)*batch_size]
            self._batch_orders_impl(base_token, quote_token, is_buy, batch_prices, batch_volumes)
            i += 1

    def _batch_orders_impl(self, base_token, quote_token, is_buy, prices: list, volumes: list):
        """"""
        assert(len(prices) == len(volumes) and len(volumes) <= self.batch_size)
        if len(prices) == 0:
            return

        data = {"security": Security.API_KEY}
        orders = []
        for p, v in zip(prices, volumes):
            order = self._create_order(base_token, quote_token, is_buy, p, v)
            orders.append(order)

        headers = {
            "Content-Type": "application/json",
        }

        data.update({
            "orders" : orders
        })

        self.add_request(
            method="POST",
            path="/api/v2/batchOrders",
            callback=self.on_send_orders,
            params={},
            data=data,
            headers=headers,
            extra=orders, # for mapping order_id and hash
        )

    def _create_order(self, base_token, quote_token, buy, price, volume):
        if buy:
            tokenS = self.market_info_map[quote_token]
            tokenB = self.market_info_map[base_token]
            amountS = str(int(10 ** tokenS['decimals'] * price * volume))
            amountB = str(int(10 ** tokenB['decimals'] * volume))
        else:
            tokenS = self.market_info_map[base_token]
            tokenB = self.market_info_map[quote_token]
            amountS = str(int(10 ** tokenS['decimals'] * volume))
            amountB = str(int(10 ** tokenB['decimals'] * price * volume))

        tokenSId = tokenS['tokenId']
        tokenBId = tokenB['tokenId']

        orderId = self.orderId[tokenSId]
        assert orderId < self.MAX_ORDER_ID
        self.orderId[tokenSId] += 1

        # make valid time ahead 1 hour
        validSince = int(time()) - self.time_offset - 3600

        # order base
        order = {
            "exchangeId"    : self.exchangeId,
            "orderId"       : orderId,
            "accountId"     : self.accountId,
            "tokenSId"      : tokenSId,
            "tokenBId"      : tokenBId,
            "amountS"       : amountS,
            "amountB"       : amountB,
            "allOrNone"     : "false",
            "validSince"    : validSince,
            "validUntil"    : validSince + 60 * 24 * 60 * 60,
            "maxFeeBips"    : 50,
            "label"         : 211,
            "buy"           : "true" if buy else "false",
            "clientOrderId" : "SampleOrder" + str(int(time()*1000))
        }

        order_message = self._serialize_order(order)
        msgHash = poseidon(order_message, self.order_sign_param)
        signedMessage = PoseidonEdDSA.sign(msgHash, FQ(int(self.private_key)))
        # update signaure
        order.update({
            "hash"        : str(msgHash),
            "signatureRx" : str(signedMessage.sig.R.x),
            "signatureRy" : str(signedMessage.sig.R.y),
            "signatureS"  : str(signedMessage.sig.s)
        })
        return order

    def _serialize_order(self, order):
        return [
            int(order["exchangeId"]),
            int(order["orderId"]),
            int(order["accountId"]),
            int(order["tokenSId"]),
            int(order["tokenBId"]),
            int(order["amountS"]),
            int(order["amountB"]),
            int(order["allOrNone"] == 'true'),
            int(order["validSince"]),
            int(order["validUntil"]),
            int(order["maxFeeBips"]),
            int(order["buy"] == 'true'),            
            int(order["label"])
        ]

    def on_send_order(self, data, request):
        if data['resultInfo']['code'] == 0:
            print(f"place order success: hash={data['data']}, clientOrderId={request.data['clientOrderId']}")
        else:
            raise AttributeError(data['resultInfo']['message'])
        pass

    def on_send_orders(self, data, request):
        if data['resultInfo']['code'] == 0:
            responses = data['data']
            for idx, order_response in enumerate(responses):
                if "error" not in order_response:
                    print(f"place order success: hash={order_response['hash']}, clientOrderId={request.extra[idx]['orderId']}")
                else:
                    print(f"Single batch order failed: {responses['error']['message']}")
        else:
            raise AttributeError(data['resultInfo']['message'])
        pass

    def cancel_order(self, **cancel_params):
        """"""
        data = {
            "security": Security.SIGNED
        }

        params = {
            "accountId": self.accountId,
        }

        if "clientOrderId" in cancel_params:
            params["clientOrderId"] = cancel_params["clientOrderId"]
        if "orderHash" in cancel_params:
            params["orderHash"] = cancel_params["orderHash"]

        print(f"cancel_order {params}")
        self.add_request(
            method="DELETE",
            path="/api/v2/orders",
            callback=self.on_cancel_orders,
            params=params,
            data=data
        )

    def on_cancel_orders(self, data, request):
        if data['resultInfo']['code'] == 0:
            print(f"cancel orders {request.data} success {data}")
        else:
            raise AttributeError(data['resultInfo']['message'])
        pass

    def cancel_orders(self, **cancel_params):
        """"""
        cancel_by_orderId = False
        cancel_by_hash = False
        cancel_reqs = None
        if "clientOrderId" in cancel_params:
            cancel_by_orderId = True
            clientOrderIds = cancel_params["clientOrderId"].split(',')
            cancel_reqs = clientOrderIds
        if "orderHash" in cancel_params:
            cancel_by_hash = True
            orderHashs = cancel_params["orderHash"].split(',')
            cancel_reqs = orderHashs

        if cancel_by_orderId and cancel_by_hash:
            print(f"Cancel by orderId and hash simultaneously is NOT support.")
            return
        elif not cancel_by_orderId and not cancel_by_hash:
            self.cancel_order()
            return

        i = 0
        batch_size = self.batch_size
        while i*batch_size < len(cancel_reqs):
            data = {
                "security": Security.SIGNED
            }
            params = {
                "accountId": self.accountId,
            }
            if cancel_by_orderId:
                params["clientOrderId"] = ','.join(cancel_reqs[i*batch_size : (i+1)*batch_size])
            elif cancel_by_hash:
                params["orderHash"] = ','.join(cancel_reqs[i*batch_size : (i+1)*batch_size])

            print(params)
            path = "/api/v2/orders/byHash" if cancel_by_hash else "/api/v2/orders/byClientOrderId"
            self.add_request(
                method="DELETE",
                path=path,
                callback=self.on_cancel_orders,
                params=params,
                data=data
            )
            i += 1






