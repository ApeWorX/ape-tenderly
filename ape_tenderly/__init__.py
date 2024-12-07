from ape import plugins


@plugins.register(plugins.Config)
def config_class():
    from ape_tenderly.provider import TenderlyConfig

    return TenderlyConfig


@plugins.register(plugins.ProviderPlugin)
def providers():
    from ape_tenderly.provider import NETWORKS

    for ecosystem_name in NETWORKS:
        for network_name, provider in NETWORKS[ecosystem_name]:
            yield ecosystem_name, network_name, provider


def __getattr__(name: str):
    if name == "NETWORKS":
        from ape_tenderly.provider import NETWORKS

        return NETWORKS

    elif name == "TenderlyConfig":
        from ape_tenderly.provider import TenderlyConfig

        return TenderlyConfig

    elif name == "TenderlyForkProvider":
        from ape_tenderly.provider import TenderlyForkProvider

        return TenderlyForkProvider

    elif name == "TenderlyGatewayProvider":
        from ape_tenderly.provider import TenderlyGatewayProvider

        return TenderlyGatewayProvider

    else:
        raise AttributeError(name)


__all__ = [
    "NETWORKS",
    "TenderlyConfig",
    "TenderlyForkProvider",
    "TenderlyGatewayProvider",
]
