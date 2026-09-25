# Quick Start

Ecosystem plugin for Tenderly support in Ape.

## Dependencies

- [Python 3](https://www.python.org/downloads) version 3.10 or greater.

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install ape-tenderly
```

### via source

You can clone the repository and install for development:

```bash
git clone https://github.com/ApeWorX/ape-tenderly.git
cd ape-tenderly
uv sync --group dev
uv run prek install
```

## Quick Usage

This plugin works as a normal provider for forked mainnet networks only (e.g. Ethereum, Fantom, etc.).

If you know your fork ID (from the Tenderly console) you can use that like this

```sh
export TENDERLY_FORK_ID=...
```

If you have an API service that automatically provisions tenderly forks, you can use it like this

```sh
export TENDERLY_FORK_SERVICE_URI=...
```
