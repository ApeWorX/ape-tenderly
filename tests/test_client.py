import os
from contextlib import contextmanager

import pytest
import requests
from ape.exceptions import ConfigError

from ape_tenderly import NETWORKS, TenderlyGatewayProvider
from ape_tenderly.client import TENDERLY_GATEWAY_ACCESS_KEY, TenderlyClient


@pytest.fixture(scope="session")
def client():
    return TenderlyClient()


@pytest.mark.parametrize(
    "ecosystem_name,network_name",
    [
        (ecosystem_name, network_name)
        for ecosystem_name in NETWORKS
        for (network_name, provider_class) in NETWORKS[ecosystem_name]  # type: ignore[attr-defined]
        if provider_class == TenderlyGatewayProvider
    ],
)
def test_gateway_uri(client, ecosystem_name, network_name):
    response = requests.post(
        client.get_gateway_rpc_uri(ecosystem_name, network_name),
        json={"id": 0, "jsonrpc": "2.0", "method": "web3_clientVersion", "params": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "Tenderly" in data["result"]


@contextmanager
def run_without_secret(secret_name):
    __cached_secret = os.environ.get(secret_name)
    del os.environ[secret_name]
    yield
    os.environ[secret_name] = __cached_secret


def test_missing_gateway_secret(client):
    with run_without_secret(TENDERLY_GATEWAY_ACCESS_KEY):
        with pytest.raises(ConfigError, match="No valid Tenderly Gateway Access Key found."):
            client.get_gateway_rpc_uri("doesnt", "matter")


@pytest.mark.skip(reason="Requires a subscription to Tenderly's premium service.")
def test_create_fork(client):
    assert len(client.get_forks()) == 0
    fork = client.create_fork(1)
    try:
        assert fork in client.get_forks()
    finally:
        client.remove_fork(fork.id)
