from ape import plugins

from .provider import TenderlyProvider


@plugins.register(plugins.ProviderPlugin)
def providers():
    yield "ethereum", "mainnet-fork", TenderlyProvider
    yield "fantom", "opera-fork", TenderlyProvider
