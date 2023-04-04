import os

from ape.api import Web3Provider, UpstreamProvider, TestProviderAPI
from ape.exceptions import ProviderError
from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.rpc import rpc_gas_price_strategy


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
