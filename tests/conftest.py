import ape
import pytest


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
def mainnet_fork(networks):
    return networks.ethereum.mainnet_fork


@pytest.fixture
def mainnet_fork_provider(mainnet_fork):
    with mainnet_fork.use_provider("tenderly") as provider:
        yield provider
