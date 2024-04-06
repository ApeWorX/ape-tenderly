import os
from typing import Any, Dict, List

import requests
from ape.exceptions import ConfigError
from ape.utils import cached_property
from ethpm_types import BaseModel

TENDERLY_PROJECT = "TENDERLY_PROJECT"
TENDERLY_ACCESS_KEY = "TENDERLY_ACCESS_KEY"
TENDERLY_GATEWAY_ACCESS_KEY = "TENDERLY_GATEWAY_ACCESS_KEY"


class ForkDetails(BaseModel):
    chain_config: Dict[str, Any] = {}


class Fork(BaseModel):
    id: str
    network_id: int
    block_number: int
    details: ForkDetails
    json_rpc_url: str
    config: Dict[str, Any] = {}


class TenderlyClientError(Exception):
    pass


class TenderlyClient:
    @cached_property
    def _authenticated_session(self) -> requests.Session:
        if not (access_key := os.environ.get(TENDERLY_ACCESS_KEY)):
            raise ConfigError("No valid tenderly access key found.")

        session = requests.Session()
        session.headers.update({"X-Access-Key": access_key})

        return session

    @cached_property
    def _api_uri(self) -> str:
        if not (project_name := os.environ.get(TENDERLY_PROJECT)):
            raise ConfigError("No valid tenderly project name found.")

        return f"https://api.tenderly.co/api/v2/project/{project_name}"

    def get_forks(self) -> List[Fork]:
        response = self._authenticated_session.get(f"{self._api_uri}/forks")

        if not response.ok:
            raise TenderlyClientError(f"Error processing request: {response.text}")

        if forks := response.json():
            return [Fork.model_validate_json(x) for x in forks]

        else:
            return []

    def create_fork(self, chain_id: int) -> Fork:
        response = self._authenticated_session.post(
            f"{self._api_uri}/forks",
            json={
                "name": f"ape-fork-{chain_id}",
                "description": "Automatically created by Ape",
                "network_id": str(chain_id),
            },
        )

        if not response.ok:
            raise TenderlyClientError(f"Error processing request: {response.text}")

        return Fork.model_validate_json(response.json().get("fork"))

    def remove_fork(self, fork_id: str):
        response = self._authenticated_session.delete(f"{self._api_uri}/forks/{fork_id}")

        if not response.ok:
            raise TenderlyClientError(f"Error processing request: {response.text}")

    def get_gateway_rpc_uri(self, ecosystem_name: str, network_name: str) -> str:
        if ecosystem_name == "ethereum":
            # e.g. Sepolia, etc.
            network_subdomain = network_name
        elif network_name == "mainnet":
            # e.g. Polygon mainnet, Optimism, etc.
            network_subdomain = ecosystem_name
        else:
            network_subdomain = f"{ecosystem_name}-{network_name}"

        if not (project_id := os.environ.get(TENDERLY_GATEWAY_ACCESS_KEY)):
            raise ConfigError("No valid Tenderly Gateway Access Key found.")

        return f"https://{network_subdomain}.gateway.tenderly.co/{project_id}"
