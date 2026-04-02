# Octahedroflake

Direct STL generator for a printable 3D octahedron fractal inspired by the Sierpinski triangle.

[![Social Preview](https://repository-images.githubusercontent.com/626647438/cb055930-87fd-490b-80b1-48fa105da8bc)](https://www.printables.com/model/432767)

## What is here

- `octahedroflake.py` handles CLI arguments, size calculations, and the mesh generator entrypoint.
- `mesh_generator.py` builds STL output directly from triangle meshes using `manifold3d`, which keeps RAM use low even for higher orders.
- `run.sh` is the main local entrypoint. It selects Python 3.11, bootstraps `venv/`, installs dependencies, and runs the generator.
- `requirements.txt` and `requirements-dev.txt` declare runtime and development dependencies.
- `octahedroflake.ipynb` is an exploratory notebook version of the generator.
- `tests/` covers CLI parsing and lightweight runtime helpers.
- Generated files are written under `output/`.

## Prerequisites

- Python 3.11 for the local wrapper script
- `manifold3d` for the mesh boolean engine

The simplest local workflow is to let `run.sh` create the virtual environment and install what it needs.

## Usage

Interactive mode:

```bash
./run.sh
```

Repeatable non-interactive run:

```bash
./run.sh --no-prompt -i 4 -l 0.2 -n 0.4 -m 200
```

Direct Python entrypoint:

```bash
python3.11 octahedroflake.py --iterations 4 --layer-height 0.2 --nozzle-diameter 0.4 --desired_height 200
```

Show CLI help:

```bash
./run.sh --help
python3.11 octahedroflake.py --help
```

Notes:

- `desired_height` now controls the actual overall model height in mm.
- `nozzle_diameter` only affects printability-driven features such as rib thickness.
- `--branded` is not currently supported in the mesh-only generator.

Outputs are written to:

```text
output/<nozzle>mm_nozzle/<layer_height>mm_layer_height/
```

## Development

Format the generator:

```bash
yapf -i octahedroflake.py mesh_generator.py
```

Lint the generator:

```bash
python3.11 -m pip install -r requirements-dev.txt
python3.11 -m pylint octahedroflake.py mesh_generator.py tests/test_octahedroflake.py
```

Run the lightweight test suite:

```bash
python3.11 -m unittest discover -s tests
```

Recommended manual validation:

```bash
./run.sh --no-prompt -i 4 -l 0.2 -n 0.4 -m 200
```

## Docker

Build the image:

```bash
docker build -t octahedroflake .
```

Run the generator with the repo `output/` directory mounted:

```bash
docker run -it -v "$(pwd)/output:/home/output" octahedroflake
```

## Pre-generated models

Pre-generated files, printing guidance, and photos are available on [Printables](https://www.printables.com/model/432767).

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

[![CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)
