# Show available commands
_default:
    @printf 'Automation tasks:\n'
    @just --list --unsorted --list-heading '' --list-prefix '  - '

# Run the strptime command
run *args='':
    uv run strptime {{ args }}

# Run all checks (format, lint, test)
check: format lint test

# Format code with ruff
format *files='':
    uv run ruff check --fix {{ files }}
    uv run ruff format {{ files }}

# Lint source code
lint *files='':
    uv run ruff check {{ files }}
    uv run ruff format --check {{ files }}

# Run tests
test *args='':
    uv run pytest -v {{ args }}

# Run tests with coverage
test-cov:
    uv run pytest --cov=strptime --cov=tests --cov-report=term-missing --cov-report=html

# Run tests on every supported Python version
test-all:
    #!/usr/bin/env bash
    set -euo pipefail
    for version in 3.9 3.10 3.11 3.12 3.13 3.14; do
        printf '\n--- Python %s ---\n' "$version"
        uv run --isolated --python "$version" pytest -q
    done

# Bump version (usage: just bump patch|minor|major)
bump value:
    uv version --bump {{ value }}

# Build the package
build:
    uv sync  # Force uv version error if applicable
    uv build --clear

# Publish to PyPI (normally done by the release workflow instead)
publish: build
    uv publish

# Tag the current version and push, which publishes to PyPI via GitHub Actions
release: check
    #!/usr/bin/env bash
    set -euo pipefail
    version="$(uv version --short)"
    branch="$(git branch --show-current)"
    if [ "$branch" != "main" ]; then
        echo "Releases happen from main, but HEAD is on $branch." >&2
        exit 1
    fi
    if [ -n "$(git status --porcelain)" ]; then
        echo "Working tree is dirty. Commit the version bump first." >&2
        exit 1
    fi
    if git rev-parse "v${version}" >/dev/null 2>&1; then
        echo "Tag v${version} already exists. Run 'just bump' first." >&2
        exit 1
    fi
    git tag -a "v${version}" -m "Version ${version}"
    git push origin main "v${version}"
    echo "Pushed v${version}. Watch the release run:"
    echo "  https://github.com/treyhunner/strptime-cli/actions"
