# ILStrap

ilstrap is a bootstrap for IDA Loaders to simplify/standardize the installation and initialization process

it has cross-platform support for installing IDA loaders, including ones that have several modules.

## Installing

Run `pip install ilstrap`

## Hacking

Get setup with poetry:
```shell
pip install poetry
poetry install
```

That will install `ilstrap` to a venv.  You can test with `poetry shell` or
run the file on a project directly with `poetry run ilstrap <locaiton_of_istrap.json>`