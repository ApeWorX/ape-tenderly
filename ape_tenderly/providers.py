import os

import requests
from ape.api import ProviderAPI, Web3Provider
from ape.utils import cached_property
from web3 import HTTPProvider, Web3


class TenderlyProvider(Web3Provider, ProviderAPI):
    @cached_property
    def fork_id(self) -> str:
        if "TENDERLY_FORK_ID" in os.environ:
            return os.environ["TENDERLY_FORK_ID"]

        elif "TENDERLY_FORK_SERVICE_URI" in os.environ:
            response = requests.post(
                os.environ["TENDERLY_FORK_SERVICE_URI"],
                json={"network_id": str(self.network.chain_id)},
            )
            return response.json()["simulation_fork"]["id"]

        else:
            raise

    @property
    def uri(self) -> str:
        return f"https://rpc.tenderly.co/fork/{self.fork_id}"

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

    def disconnect(self):
        self._web3 = None
