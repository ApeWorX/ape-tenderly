import os

import requests
from ape.api import UpstreamProvider, Web3Provider
from ape.exceptions import ConfigError, ProviderError
from ape.utils import cached_property
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware

TENDERLY_FORK_ID = "TENDERLY_FORK_ID"
TENDERLY_FORK_SERVICE_URI = "TENDERLY_FORK_SERVICE_URI"


class TenderlyForkProvider(Web3Provider):
    @cached_property
    def fork_id(self) -> str:
        if TENDERLY_FORK_ID in os.environ:
            return os.environ[TENDERLY_FORK_ID]

        elif TENDERLY_FORK_SERVICE_URI in os.environ:
            fork_network_name = self.network.name.replace("-fork", "")
            chain_id = self.network.ecosystem.get_network(fork_network_name).chain_id
            response = requests.post(
                os.environ[TENDERLY_FORK_SERVICE_URI],
                json={"network_id": str(chain_id)},
            )
            return response.json()["simulation_fork"]["id"]

        else:
            raise ConfigError("No valid tenderly fork ID found.")

    @property
    def uri(self) -> str:
        return f"https://rpc.tenderly.co/fork/{self.fork_id}"

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

    def disconnect(self):
        self._web3 = None


class TenderlyGatewayProvider(Web3Provider, UpstreamProvider):
    """
    A web3 provider using an HTTP connection to Tenderly's RPC nodes.

    Docs: https://docs.tenderly.co/web3-gateway/web3-gateway
    """

    @property
    def uri(self) -> str:
        project_id = os.environ.get("TENDERLY_GATEWAY_ACCESS_KEY")
        assert project_id is not None
        network_name = self.network.name
        return f"https://{network_name}.gateway.tenderly.co/{project_id}"

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
