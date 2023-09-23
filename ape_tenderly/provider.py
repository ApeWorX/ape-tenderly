import atexit

from ape.api import PluginConfig, UpstreamProvider, Web3Provider
from ape.exceptions import ProviderError
from ape.logging import logger
from ape.utils import cached_property
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware

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
        return f"https://rpc.tenderly.co/fork/{self.fork.id}"

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))
        atexit.register(self.disconnect)  # NOTE: Make sure we de-provision forks

    def disconnect(self):
        if self.config.auto_remove_forks:
            try:
                fork_id = self.fork.id
                logger.debug(f"Removing tenderly fork '{fork_id}'...")
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
        ecosystem_name = self.network.ecosystem.name
        network_name = self.network.name

        if ecosystem_name == "ethereum":
            # e.g. Sepolia, Goerli, etc.
            network_subdomain = network_name
        elif network_name == "mainnet":
            # e.g. Polygon mainnet, Optimism, etc.
            network_subdomain = ecosystem_name
        else:
            network_subdomain = f"{ecosystem_name}-{network_name}"

        return self._client.get_gateway_rpc_uri(network_subdomain)

    @property
    def connection_str(self) -> str:
        return self.uri

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

        try:
            # Any chain that *began* as PoA needs the middleware for pre-merge blocks
            ethereum_goerli = 5
            optimism = (10, 420)
            polygon = (137, 80001)

            if self._web3.eth.chain_id in (ethereum_goerli, *optimism, *polygon):
                self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

            self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        except Exception as err:
            raise ProviderError(f"Failed to connect to Tenderly Gateway.\n{repr(err)}") from err

    def disconnect(self):
        self._web3 = None
