# IOXIO® Data Product Definitions tooling

Tools for managing Data Product definitions

# Installation

```shell
poetry install
```

# Usage

```shell
poetry run convert-definitions --help

poetry run validate-definitions --help

# run tests
poetry run invoke test

# release a new version (after bumping it in pyproject.toml)
poetry run invoke release
```

## Pre-commit hooks

```yaml
repos:
  - repo: https://github.com/ioxio-dataspace/ioxio-data-product-definition-tooling
    rev: main # You probably want to lock this to a specific tag
    hooks:
      - id: data-product-definition-converter
        pass_filenames: false
        args: ["src", "DataProducts"]
        files: |
          (?x)^(
            DataProducts/.*json|
            src/.*py
          )$
      - id: data-product-definition-validator
        files: ".*?DataProducts/.*?json$"
        args: ["./DataProducts"]
```
