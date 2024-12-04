from ape import plugins

from .provider import TenderlyConfig, TenderlyForkProvider, TenderlyGatewayProvider

NETWORKS = {
    "ethereum": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "polygon": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("amoy", TenderlyGatewayProvider),
        ("amoy-fork", TenderlyForkProvider),
    ],
    "arbitrum": [
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "optimism": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "base": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("sepolia", TenderlyGatewayProvider),
        ("sepolia-fork", TenderlyForkProvider),
    ],
    "avalance": [
        ("mainnet-fork", TenderlyForkProvider),
    ],
    "fantom": [
        ("opera-fork", TenderlyForkProvider),
    ],
}


@plugins.register(plugins.Config)
def config_class():
    return TenderlyConfig


@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem_name in NETWORKS:
        for network_name, provider in NETWORKS[ecosystem_name]:
            yield ecosystem_name, network_name, provider
