import atexit

from ape.api import PluginConfig, UpstreamProvider
from ape.exceptions import ProviderError
from ape.logging import logger
from ape.utils import cached_property
from ape_ethereum.provider import Web3Provider
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy

try:
    from web3.middleware import ExtraDataToPOAMiddleware  # type: ignore
except ImportError:
    from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware  # type: ignore

from .client import Fork, TenderlyClient


class TenderlyConfig(PluginConfig):
    auto_remove_forks: bool = True


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
        optimism = (10, 420)
        polygon = (137, 80001)

        if chain_id in (*optimism, *polygon):
            self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

    def disconnect(self):
        self._web3 = None


NETWORKS = {
    "ethereum": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "polygon": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("amoy", TenderlyGatewayProvider),
        ("amoy-fork", TenderlyForkProvider),
    ],
    "arbitrum": [
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "optimism": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "base": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "avalanche": [
        ("mainnet-fork", TenderlyForkProvider),
    ],
    "fantom": [
        ("opera-fork", TenderlyForkProvider),
    ],
}
