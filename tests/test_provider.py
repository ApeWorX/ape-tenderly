import os

import pytest
from ape.exceptions import ConfigError

from ape_tenderly.provider import TENDERLY_FORK_ID


@pytest.fixture(autouse=True)
def connected_eth_mainnet_provider(mainnet_fork_provider):
    """
    See README for info on how to set the environment variable.
    Else, tests will not run.
    """
    if TENDERLY_FORK_ID not in os.environ:
        pytest.fail(f"{TENDERLY_FORK_ID} environment variable is required to run tests.")

    return mainnet_fork_provider


@pytest.fixture
def unset_fork_id(mainnet_fork_provider):
    fork_id = os.environ.pop(TENDERLY_FORK_ID)
    was_cached = "fork_id" in mainnet_fork_provider.__dict__
    if was_cached:
        del mainnet_fork_provider.__dict__["fork_id"]

    yield

    os.environ[TENDERLY_FORK_ID] = fork_id
    if was_cached:
        mainnet_fork_provider.__dict__["fork_id"] = fork_id


def test_fork_id_and_uri(connected_eth_mainnet_provider):
    provider = connected_eth_mainnet_provider
    assert provider.fork_id
    assert provider.uri


def test_fork_id_missing(mainnet_fork_provider, unset_fork_id):
    with pytest.raises(ConfigError, match="No valid tenderly fork ID found."):
        _ = mainnet_fork_provider.fork_id
