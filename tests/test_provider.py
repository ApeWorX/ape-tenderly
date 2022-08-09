def test_reset_fork(mainnet_fork_provider):
    assert mainnet_fork_provider.fork_id
    assert mainnet_fork_provider.uri
