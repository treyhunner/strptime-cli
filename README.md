# strptime

[![PyPI - Version](https://img.shields.io/pypi/v/strptime.svg)](https://pypi.org/project/strptime)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/strptime.svg)](https://pypi.org/project/strptime)

## Installation

```console
pipx install strptime
```

## Usage

Run `strptime` with a date string to see the format string you would need to pass to `datetime.datetime.strptime` to parse the date:

```console
$ strptime "2030-01-24 05:45"
%Y-%m-%d %H:%M
```

## License

This package is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
