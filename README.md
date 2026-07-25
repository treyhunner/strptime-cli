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


## Development

This project uses [uv](https://docs.astral.sh/uv/) and [just](https://just.systems).
Run `just` to see every available task.

```console
$ just test     # run the test suite
$ just check    # format, lint, and test
```

No setup step is needed: `uv` creates the virtual environment and installs dependencies on the first `uv run`.

To run the tests on every supported Python version:

```console
just test-all
```

If you would rather not install `just`, every task is a short `uv` command that you can run directly (check the `justfile` for the commands):

```console
uv run pytest
```


## Releasing

Releases are published to PyPI by GitHub Actions whenever a `v*` tag is pushed.
From an up-to-date `main`:

```console
$ just bump minor              # or patch, or major
$ git commit -am "Version 0.5.0"
$ just release
```

The `release` task refuses to run unless the checks pass, the working tree is clean, and you are on `main`.
It then tags the current version and pushes, which triggers the release workflow.


## License

This package is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
