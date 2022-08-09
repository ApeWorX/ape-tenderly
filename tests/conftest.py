from pathlib import Path

import pytest

from ape_tenderly.providers import TenderlyProvider


@pytest.fixture
def networks():
    from ape import networks

    return networks


@pytest.fixture
def accounts():
    from ape import accounts

    return accounts


@pytest.fixture
def Contract():
    from ape import Contract

    return Contract


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
