# ape-tenderly

Ecosystem Plugin for Tenderly support in Ape

## Dependencies

* [python3](https://www.python.org/downloads) version 3.7.2 or greater, python3-dev

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install ape-tenderly
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/ape-tenderly.git
cd ape-tenderly
python3 setup.py install
```

## Quick Usage

This plugin works as a normal provider for forked mainnet networks only (e.g. Ethereum, Fantom, etc.)

If you know your fork ID (from the Tenderly console) you can use that like this
```sh
export TENDERLY_FORK_ID=...
```

If you have an API service that automatically provisions tenderly forks, you can use it like this
```sh
export TENDERLY_FORK_SERVICE_URI=...
```

## Development

This project is in development and should be considered a beta.
Things might not be in their final state and breaking changes may occur.
Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0](LICENSE).
