import atexit

from ape.api import PluginConfig, UpstreamProvider
from ape.exceptions import ProviderError
from ape.logging import logger
from ape.utils import cached_property
from ape_ethereum.provider import Web3Provider
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware
from typing import List, Optional, cast

from ape.types import (
    AddressType,
)

from ape.exceptions import (
    VirtualMachineError,
)
from ape.utils import cached_property
from ethpm_types import HexBytes
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware
from web3.types import TxParams

from .client import Fork, TenderlyClient


class TenderlyConfig(PluginConfig):
    auto_remove_forks: bool = True

    host: Optional[str] = None
    """The host address """




class TenderlyForkProvider(Web3Provider):
    @cached_property
    def _client(self) -> TenderlyClient:
        return TenderlyClient()

    def _create_fork(self) -> Fork:
        ecosystem_name = self.network.ecosystem.name
        network_name = self.network.name.replace("-fork", "")
        chain_id = self.network.ecosystem.get_network(network_name).chain_id

        logger.debug(f"Creating tenderly fork for '{ecosystem_name}:{network_name}'...")
        fork = self._client.create_fork(chain_id)
        logger.success(f"Created tenderly fork '{fork.id}'.")
        return fork

    @cached_property
    def fork(self) -> Fork:
        # NOTE: Always create a new fork, because the fork will get cached here
        #       per-instance of this class, and "released" when the fork is closed
        return self._create_fork()

    @property
    def uri(self) -> str:
        return self.fork.json_rpc_url

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))
        atexit.register(self.disconnect)  # NOTE: Make sure we de-provision forks

    def disconnect(self):
        if self.config.auto_remove_forks:
            fork_id = self.fork.id
            logger.debug(f"Removing tenderly fork '{fork_id}'...")

            try:
                self._client.remove_fork(fork_id)
                logger.success(f"Removed tenderly fork '{fork_id}'.")

            except Exception as e:
                logger.error(f"Couldn't remove tenderly fork '{fork_id}': {e}.")

        else:
            logger.info(f"Not removing tenderly fork '{self.fork.id}.'")

        self._web3 = None


class TenderlyGatewayProvider(Web3Provider, UpstreamProvider):
    """
    A web3 provider using an HTTP connection to Tenderly's RPC nodes.

    Docs: https://docs.tenderly.co/web3-gateway/web3-gateway
    """

    @cached_property
    def _client(self) -> TenderlyClient:
        return TenderlyClient()

    @property
    def uri(self) -> str:
        return self._client.get_gateway_rpc_uri(self.network.ecosystem.name, self.network.name)

    @property
    def connection_str(self) -> str:
        return self.uri

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

        try:
            chain_id = self._web3.eth.chain_id
        except Exception as err:
            raise ProviderError(f"Failed to connect to Tenderly Gateway.\n{repr(err)}") from err

        # Any chain that *began* as PoA needs the middleware for pre-merge blocks
        ethereum_goerli = 5
        optimism = (10, 420)
        polygon = (137, 80001)

        if chain_id in (ethereum_goerli, *optimism, *polygon):
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

    def disconnect(self):
        self._web3 = None


class TenderlyDevnetProvider(Web3Provider, TestProviderAPI):
    """
    A web3 provider using an HTTP connection to Tenderly's Devnet RPC nodes.

    Docs: https://docs.tenderly.co/devnets/intro-to-devnets
    """
    _host: Optional[str] = None

    @cached_property
    def _client(self) -> TenderlyClient:
        return TenderlyClient()

    @property
    def uri(self) -> str:
        if self._host is not None:
            return self._host

        elif config_host := self.settings.host:
            self._host = config_host

        else:
            raise ProviderError(f"Host not provided")

        return self._host

    @property
    def http_uri(self) -> str:
        # NOTE: Overriding `Web3Provider.http_uri` implementation
        return self.uri

    @property
    def connection_str(self) -> str:
        return self.uri

    @property
    def settings(self) -> TenderlyConfig:
        return cast(TenderlyConfig, super().settings)

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

        try:
            chain_id = self._web3.eth.chain_id
        except Exception as err:
            raise ProviderError(f"Failed to connect to Tenderly Devnet.\n{repr(err)}") from err

        # Any chain that *began* as PoA needs the middleware for pre-merge blocks
        ethereum_goerli = 5
        optimism = (10, 420)
        polygon = (137, 80001)

        if chain_id in (ethereum_goerli, *optimism, *polygon):
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

    def disconnect(self):
        self._web3 = None

    @property
    def unlocked_accounts(self) -> List[AddressType]:
        return list(self.account_manager.test_accounts._impersonated_accounts)

    def unlock_account(self, address: AddressType) -> bool:
        # All accounts can be unlocked
        return True

    def send_transaction(self, txn: TransactionAPI) -> ReceiptAPI:
        """
        Creates a new message call transaction or a contract creation
        for signed transactions.
        """
        sender = txn.sender
        if sender:
            sender = self.conversion_manager.convert(txn.sender, AddressType)

        if sender and sender in self.unlocked_accounts:
            # Allow for an unsigned transaction
            sender = cast(AddressType, sender)  # We know it's checksummed at this point.
            txn = self.prepare_transaction(txn)
            original_code = HexBytes(self.get_code(sender))
            if original_code:
                self.set_code(sender, "")

            txn_dict = txn.dict()
            if isinstance(txn_dict.get("type"), int):
                txn_dict["type"] = HexBytes(txn_dict["type"]).hex()

            tx_params = cast(TxParams, txn_dict)
            try:
                txn_hash = self.web3.eth.send_transaction(tx_params)
            except ValueError as err:
                raise self.get_virtual_machine_error(err, txn=txn) from err

            finally:
                if original_code:
                    self.set_code(sender, original_code.hex())
        else:
            try:
                txn_hash = self.web3.eth.send_raw_transaction(txn.serialize_transaction())
            except ValueError as err:
                vm_err = self.get_virtual_machine_error(err, txn=txn)

                if "nonce too low" in str(vm_err):
                    # Add additional nonce information
                    new_err_msg = f"Nonce '{txn.nonce}' is too low"
                    raise VirtualMachineError(
                        new_err_msg,
                        base_err=vm_err.base_err,
                        code=vm_err.code,
                        txn=txn,
                        source_traceback=vm_err.source_traceback,
                        trace=vm_err.trace,
                        contract_address=vm_err.contract_address,
                    )

                raise vm_err from err

        receipt = self.get_receipt(
            txn_hash.hex(),
            required_confirmations=(
                txn.required_confirmations
                if txn.required_confirmations is not None
                else self.network.required_confirmations
            ),
        )

        if receipt.failed:
            txn_dict = receipt.transaction.dict()
            if isinstance(txn_dict.get("type"), int):
                txn_dict["type"] = HexBytes(txn_dict["type"]).hex()

            txn_params = cast(TxParams, txn_dict)

            # Replay txn to get revert reason
            # NOTE: For some reason, `nonce` can't be in the txn params or else it fails.
            if "nonce" in txn_params:
                del txn_params["nonce"]

            try:
                self.web3.eth.call(txn_params)
            except Exception as err:
                vm_err = self.get_virtual_machine_error(err, txn=receipt)
                raise vm_err from err

        logger.info(f"Confirmed {receipt.txn_hash} (total fees paid = {receipt.total_fees_paid})")
        self.chain_manager.history.append(receipt)
        return receipt