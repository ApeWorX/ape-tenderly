import os
from typing import Any, Dict, List

import requests
from ape.exceptions import ConfigError
from ape.utils import cached_property
from pydantic import BaseModel, parse_obj_as

TENDERLY_FORK_ID = "TENDERLY_FORK_ID"
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
    def __access_key_header(self) -> Dict:
        if not (access_key := os.environ.get(TENDERLY_ACCESS_KEY)):
            raise ConfigError("No valid tenderly access key found.")

        return {"X-Access-Key": access_key}

    @cached_property
    def _api_uri(self) -> str:
        if not (project_name := os.environ.get(TENDERLY_PROJECT)):
            raise ConfigError("No valid tenderly project name found.")

        return f"https://api.tenderly.co/api/v2/project/{project_name}"

    def get_forks(self) -> List[Fork]:
        response = requests.get(
            f"{self._api_uri}/forks",
            headers=self.__access_key_header,
        )

        if not response.ok:
            # NOTE: This will raise on any HTTP errors
            response.raise_for_status()
            # ...and this will raise for anything else
            raise TenderlyClientError(f"Error processing request: {response.text}")

        return parse_obj_as(List[Fork], response.json())

    def create_fork(self, chain_id: int) -> Fork:
        response = requests.post(
            f"{self._api_uri}/forks",
            json={
                "name": f"ape-fork-{chain_id}",
                "description": "Automatically created by Ape",
                "network_id": str(chain_id),
            },
            headers=self.__access_key_header,
        )

        if not response.ok:
            # NOTE: This will raise on any HTTP errors
            response.raise_for_status()
            # ...and this will raise for anything else
            raise TenderlyClientError(f"Error processing request: {response.text}")

        return parse_obj_as(Fork, response.json().get("fork"))

    def remove_fork(self, fork_id: str):
        response = requests.delete(
            f"{self._api_uri}/forks/{fork_id}",
            headers=self.__access_key_header,
        )

        if not response.ok:
            # NOTE: This will raise on any HTTP errors
            response.raise_for_status()
            # ...and this will raise for anything else
            raise TenderlyClientError(f"Error processing request: {response.text}")

    def get_gateway_rpc_uri(self, network_name: str) -> str:
        if not (project_id := os.environ.get(TENDERLY_GATEWAY_ACCESS_KEY)):
            raise TenderlyClientError("No valid Tenderly Gateway Access Key found.")

        return f"https://{network_name}.gateway.tenderly.co/{project_id}"
