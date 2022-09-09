from pathlib import Path

import ape
import pytest

from ape_tenderly.providers import TenderlyProvider


@pytest.fixture
def networks():
    return ape.networks


@pytest.fixture
def accounts():
    return ape.accounts


@pytest.fixture
def Contract():
    return ape.Contract


@pytest.fixture
def mainnet_fork_provider(networks):
    network_api = networks.ecosystems["ethereum"]["mainnet-fork"]
    provider = TenderlyProvider(
        name="tenderly",
        network=network_api,
        request_header={},
        data_folder=Path("."),
        provider_settings={},
    )
    provider.connect()
    yield provider
    provider.disconnect()
