from ape import plugins

from .provider import TenderlyForkProvider, TenderlyGatewayProvider

NETWORKS = {
    "ethereum": [
        ("mainnet", TenderlyGatewayProvider),
        ("mainnet-fork", TenderlyForkProvider),
        ("goerli", TenderlyGatewayProvider),
        ("sepolia", TenderlyGatewayProvider),
    ],
    "fantom": [
        ("opera-fork", TenderlyForkProvider),
    ],
}


@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem_name in NETWORKS:
        for network_name, provider in NETWORKS[ecosystem_name]:
            yield ecosystem_name, network_name, provider
