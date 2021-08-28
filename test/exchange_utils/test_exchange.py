import pytest
import unittest
from web3 import Web3

from sdk.eth_utils.exchange_utils import EthExchangeWrapper

class TestApiSigns(unittest.TestCase):
    def setUp(self):
        self.exchange = EthExchangeWrapper(
            "your address",
            "your private key",
            "exchange address",
            "goerli", # chain name, conf can be found in exchange_utils
            "https://goerli.infura.io/v3/XXXXXXXXXXXX" # eth node provider
        )
        print(f"setUpClass exchange done.")
        return super().setUp()

    def test_exchange_init(self):
        print(bytes.hex(self.exchange.getDomainSeparator()))
        print(self.exchange.getDepositContract())

    def test_exchange_deposit_ETH(self):
        self.exchange.deposit("ETH", 0.01)

    def test_exchange_deposit_LRC(self):
        self.exchange.deposit("LRC", 1000)