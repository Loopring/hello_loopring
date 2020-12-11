import json
import os
import time
from web3 import Web3


class EthExchangeWrapper:
    def __init__(self, address, private_key, exchange_address, testnet, provider=None, web3=None):

        if not web3:
            # Initialize web3. Extra provider for testing.
            if not provider:
                self.provider = os.environ["PROVIDER"]
                self.network = testnet
            else:
                self.provider = provider
                self.network = testnet
            if self.provider.startswith('http'):
                self.w3 = Web3(Web3.HTTPProvider(self.provider, request_kwargs={"timeout": 60}))
            elif self.provider.startswith('ws'):
                self.w3 = Web3(Web3.WebsocketProvider(self.provider))
            else:
                raise AttributeError(f"Unknown provider {provider}")
        else:
            self.w3 = web3
            self.network = "mainnet"
        self.address = Web3.toChecksumAddress(address)
        self.private_key = private_key

        # This code automatically approves you for trading on the exchange.
        # max_approval is to allow the contract to exchange on your behalf.
        # max_approval_check checks that current approval is above a reasonable number
        # The program cannot check for max_approval each time because it decreases
        # with each trade.
        self.eth_address = "0x0000000000000000000000000000000000000000"
        self.max_approval_hex = "0x" + "f" * 64
        self.max_approval_int = int(self.max_approval_hex, 16)
        self.max_approval_check_hex = "0x" + "0" * 15 + "f" * 49
        self.max_approval_check_int = int(self.max_approval_check_hex, 16)

        # Initialize address and contract
        path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
        with open(os.path.abspath(path + "erc20_assets.json")) as f:
            token_addresses = json.load(f)[self.network]
        with open(os.path.abspath(path + "exchangeV3.abi")) as f:
            exchange_abi = json.load(f)
        with open(os.path.abspath(path + "erc20.abi")) as f:
            erc20_abi = json.load(f)

        # Define exchange address, contract instance, and token_instance based on
        # token address

        self.exchange_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(exchange_address), abi=exchange_abi
        )
        self.deposit_contract = self.getDepositContract()

        self.erc20_contract = {}
        for token_name, token_address in token_addresses.items():
            if token_address != self.eth_address:
                self.erc20_contract[token_name] = self.w3.eth.contract(
                    address= Web3.toChecksumAddress(token_address), abi=erc20_abi
                )

    def getDomainSeparator(self):
        exchange_funcs = self.exchange_contract.functions
        return exchange_funcs.getDomainSeparator().call()

    def getDepositContract(self):
        exchange_funcs = self.exchange_contract.functions
        return exchange_funcs.getDepositContract().call()

    # ------ Decorators ----------------------------------------------------------------
    def check_approval(method):
        """Decorator to check if user is approved for a token. It approves them if they
            need to be approved."""

        def approved(self, *args):
            # Check to see if the first token is actually ETH
            token = args[0]
            token_contract = self.erc20_contract.get(token, None)
            amount = int(args[1]*1e18)

            # Approve both tokens, if needed
            if token_contract:
                is_approved = self._is_approved(token)
                if not is_approved:
                    self.approve_erc20_transfer(token, amount)

            return method(self, *args)

        return approved

    # ------ Funcs ----------------------------------------------------------------
    @check_approval
    def deposit(self, token, amount):
        exchange_funcs = self.exchange_contract.functions
        token_address = self.eth_address
        eth_qty = int(amount * 1e18)
        token_qty = 0
        if token in self.erc20_contract:
            token_address = self.erc20_contract[token].address
            token_qty = int(amount * 1e18)
            eth_qty= 0
        tx_params = self._get_tx_params(value=eth_qty, gas=500000)
        func_params = [self.address, self.address, token_address, token_qty, bytes(0)]
        function = exchange_funcs.deposit(*func_params)
        return self._build_and_send_tx(function, tx_params)

    def approveTransaction(self, txHash):
        exchange_funcs = self.exchange_contract.functions
        tx_params = self._get_tx_params(value=0, gas=300000)
        func_params = [self.address, txHash]
        function = exchange_funcs.approveTransaction(*func_params)
        return self._build_and_send_tx(function, tx_params)

    # ------ Approval Utils ------------------------------------------------------------
    def approve_erc20_transfer(self, token, max_approval=None):
        """Give an exchange max approval of a token."""
        max_approval = self.max_approval_int if not max_approval else max_approval
        tx_params = self._get_tx_params()
        exchange_addr = self.exchange_contract.address
        function = self.erc20_contract[token].functions.approve(
            self.deposit_contract, max_approval
        )
        tx = self._build_and_send_tx(function, tx_params)
        self.w3.eth.waitForTransactionReceipt(tx, timeout=6000)
        # Add extra sleep to let tx propogate correctly
        time.sleep(1)

    def _is_approved(self, token):
        """Check to see if the exchange and token is approved."""
        exchange_addr = self.exchange_contract.address
        amount = (
            self.erc20_contract[token].functions.allowance(self.address, exchange_addr).call()
        )
        if amount >= self.max_approval_check_int:
            return True
        else:
            return False

    # ------ Tx Utils ------------------------------------------------------------------
    def _deadline(self):
        """Get a predefined deadline."""
        return int(time.time()) + 1000

    def _build_and_send_tx(self, function, tx_params):
        """Build and send a transaction."""
        transaction = function.buildTransaction(tx_params)
        signed_txn = self.w3.eth.account.signTransaction(
            transaction, private_key=self.private_key
        )
        return self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    def _get_tx_params(self, value=0, gas=150000):
        """Get generic transaction parameters."""
        return {
            "from": self.address,
            "value": value,
            "gas": gas,
            "nonce": self.w3.eth.getTransactionCount(self.address),
        }
