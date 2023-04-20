from ape import plugins

from .provider import TenderlyGatewayProvider

NETWORKS = {
    "ethereum": [
        "mainnet",
        "goerli",
        "sepolia",
    ],
}


@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem_name in NETWORKS:
        for network_name in NETWORKS[ecosystem_name]:
            yield ecosystem_name, network_name, TenderlyGatewayProvider
