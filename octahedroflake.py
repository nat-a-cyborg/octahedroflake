#!/usr/bin/env python3
"""
Generate a printable octahedron fractal known as the Octahedroflake.

The model is built as a direct triangle mesh and exported as STL. The CLI
accepts a desired overall model height and derives the pyramid edge length
required for the requested iteration count and print settings.
"""

import argparse
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mesh_generator import MeshOctahedroflakeGenerator

ITERATIONS_DEFAULT = 4
LAYER_HEIGHT_DEFAULT = 0.2
NOZZLE_DIAMETER_DEFAULT = 0.4
DESIRED_HEIGHT_DEFAULT = 200
BRANDED_DEFAULT = False

HEIGHT_FACTOR = 0.7071  # see: calculatorsoup.com/calculators/geometry-solids/pyramid.php
GAP_SIZE = 0.1

BASE_DIR = Path(__file__).resolve().parent

_NUMPY_MODULE = None
_MANIFOLD_MODULE = None


@dataclass(frozen=True)
class ModelConfig:
    """Runtime configuration for a single generator invocation."""

    iterations: int = ITERATIONS_DEFAULT
    layer_height: float = LAYER_HEIGHT_DEFAULT
    nozzle_diameter: float = NOZZLE_DIAMETER_DEFAULT
    desired_height: float = DESIRED_HEIGHT_DEFAULT
    branded: bool = BRANDED_DEFAULT


@dataclass(frozen=True)
class ModelDimensions:  # pylint: disable=too-many-instance-attributes
    """Derived measurements used throughout the generated mesh."""

    edge_size: float
    rib_width: float
    gap_size: float
    full_size: float
    full_height: int
    pyramid_height: float
    combined_height: float
    gap_height: float


def positive_int(value):
    """Parse a required positive integer CLI value."""

    parsed_value = int(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError('value must be a positive integer')
    return parsed_value


def positive_float(value):
    """Parse a required positive float CLI value."""

    parsed_value = float(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError('value must be a positive number')
    return parsed_value


def build_parser():
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description='octahedroflake')
    parser.add_argument('-i', '--iterations', type=positive_int, default=ITERATIONS_DEFAULT, help='number of iterations')
    parser.add_argument(
        '-l', '--layer-height', type=positive_float, default=LAYER_HEIGHT_DEFAULT, help='layer height in mm'
    )
    parser.add_argument(
        '-n', '--nozzle-diameter', type=positive_float, default=NOZZLE_DIAMETER_DEFAULT, help='nozzle diameter in mm'
    )
    parser.add_argument('--desired_height', type=positive_float, default=DESIRED_HEIGHT_DEFAULT, help='desired height')
    parser.add_argument('--branded', dest='branded', action='store_true', help='include branding in the model')
    parser.set_defaults(branded=BRANDED_DEFAULT)
    return parser


def parse_arguments(arguments=None):
    """Parse CLI arguments while tolerating unrelated notebook flags."""

    parser = build_parser()
    local_args, _ = parser.parse_known_args(arguments)
    return ModelConfig(
        iterations=local_args.iterations,
        layer_height=local_args.layer_height,
        nozzle_diameter=local_args.nozzle_diameter,
        desired_height=local_args.desired_height,
        branded=local_args.branded,
    )


def calculate_dimensions(config):
    """Compute the model measurements derived from the requested config."""

    edge_size = (config.desired_height - config.layer_height) / ((2**config.iterations) * HEIGHT_FACTOR * 2)
    full_size = (2**config.iterations) * edge_size
    pyramid_height = edge_size * HEIGHT_FACTOR
    full_height = config.layer_height + pyramid_height * (2**(config.iterations + 1))
    return ModelDimensions(
        edge_size=edge_size,
        rib_width=config.nozzle_diameter * 2,
        gap_size=GAP_SIZE,
        full_size=full_size,
        full_height=math.ceil(full_height),
        pyramid_height=pyramid_height,
        combined_height=pyramid_height + config.layer_height,
        gap_height=config.layer_height + GAP_SIZE * HEIGHT_FACTOR,
    )


def load_mesh_modules():
    """Load direct-mesh dependencies lazily so `--help` works without them."""

    global _NUMPY_MODULE
    global _MANIFOLD_MODULE

    if _NUMPY_MODULE is not None and _MANIFOLD_MODULE is not None:
        return _NUMPY_MODULE, _MANIFOLD_MODULE

    try:
        import numpy  # pylint: disable=import-outside-toplevel
        import manifold3d  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as exc:
        raise SystemExit(
            'The generator requires numpy and manifold3d. Install dependencies first or use ./run.sh.'
        ) from exc

    _NUMPY_MODULE = numpy
    _MANIFOLD_MODULE = manifold3d
    return _NUMPY_MODULE, _MANIFOLD_MODULE


def report(message, *, time_stamp=True, order=None, extra_line=False):
    """Emit progress output."""

    if order is not None:
        message = f'{order} {message}'
    if time_stamp:
        message = f'{datetime.now()}: {message}'
    if extra_line:
        message = '\n' + message
    print(message)


def format_elapsed_time(seconds_elapsed):
    """Format a runtime duration for console output."""

    if seconds_elapsed < 120:
        return f'{seconds_elapsed} seconds'
    if seconds_elapsed < 3600:
        return f'{round(seconds_elapsed / 60, 2)} minutes'
    return f'{round(seconds_elapsed / 3600, 2)} hours'


def run(arguments=None):
    """CLI entrypoint used by both `__main__` and tests."""

    config = parse_arguments(arguments)
    dimensions = calculate_dimensions(config)
    numpy_module, manifold_module = load_mesh_modules()
    generator = MeshOctahedroflakeGenerator(
        config,
        dimensions,
        base_dir=BASE_DIR,
        numpy_module=numpy_module,
        manifold_module=manifold_module,
        reporter=report,
        format_elapsed_time=format_elapsed_time,
    )
    generator.run()


if __name__ == "__main__":
    run()
