# strptime

[![PyPI - Version](https://img.shields.io/pypi/v/strptime-cli.svg)](https://pypi.org/project/strptime-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/strptime-cli.svg)](https://pypi.org/project/strptime-cli)


## Installation

Installing with [`uv tool`](https://docs.astral.sh/uv/concepts/tools/):

```console
uv tool install strptime-cli
```

Installing with [`pipx`](https://pipx.pypa.io):

```console
pipx install strptime-cli
```

You can also install globally `strptime-cli` with `pip`, but I usually recommend installing command-line tools in their own separate environment.


## Usage

Run `strptime` with a date string to see the format string you would need to pass to `datetime.datetime.strptime` to parse the date:

```console
$ strptime "2030-01-24 05:45"
%Y-%m-%d %H:%M
```


## Testing

From within a virtual environment:

```console
$ pip install pytest
$ python tests.py
```

Or using the `uv` tool's `uvx` (no dependencies required, so `uvx` works):

```console
uvx pytest
```


## License

This package is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
