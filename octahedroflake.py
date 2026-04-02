#!/usr/bin/env python3
"""
Generate a printable octahedron fractal known as the Octahedroflake.

The model is built with CadQuery and exported as STL/STEP assets. The CLI
accepts a desired overall model height and derives the pyramid edge length
required for the requested iteration count and print settings.
"""

import argparse
import inspect
import math
import re
import timeit
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path

ITERATIONS_DEFAULT = 4
LAYER_HEIGHT_DEFAULT = 0.2
NOZZLE_DIAMETER_DEFAULT = 0.4
DESIRED_HEIGHT_DEFAULT = 200
BRANDED_DEFAULT = False

HEIGHT_FACTOR = 0.7071  # see: calculatorsoup.com/calculators/geometry-solids/pyramid.php
GAP_SIZE = 0.01
USE_DISK_CACHE = True

BASE_DIR = Path(__file__).resolve().parent

_CADQUERY_MODULE = None
_EXPORTERS_MODULE = None


@dataclass(frozen=True)
class ModelConfig:
    """Runtime configuration for a single generator invocation."""

    iterations: int = ITERATIONS_DEFAULT
    layer_height: float = LAYER_HEIGHT_DEFAULT
    nozzle_diameter: float = NOZZLE_DIAMETER_DEFAULT
    desired_height: float = DESIRED_HEIGHT_DEFAULT
    branded: bool = BRANDED_DEFAULT


@dataclass(frozen=True)
class ModelDimensions:
    """Derived measurements used throughout the CAD model."""

    edge_size: float
    rib_width: float
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

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--branded', dest='branded', action='store_true', help='include branding in the model')
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

    edge_size = config.desired_height / ((2**config.iterations) * (config.nozzle_diameter * 4) * HEIGHT_FACTOR * 2)
    full_size = (2**config.iterations) * edge_size
    pyramid_height = round(edge_size * HEIGHT_FACTOR, 2)
    return ModelDimensions(
        edge_size=edge_size,
        rib_width=config.nozzle_diameter * 2,
        full_size=full_size,
        full_height=math.ceil(full_size * HEIGHT_FACTOR * 2),
        pyramid_height=pyramid_height,
        combined_height=pyramid_height + config.layer_height,
        gap_height=config.layer_height + GAP_SIZE * HEIGHT_FACTOR,
    )


def load_cadquery():
    """Load CadQuery lazily so `--help` works without CAD dependencies installed."""

    global _CADQUERY_MODULE
    global _EXPORTERS_MODULE

    if _CADQUERY_MODULE is not None and _EXPORTERS_MODULE is not None:
        return _CADQUERY_MODULE, _EXPORTERS_MODULE

    try:
        import cadquery  # pylint: disable=import-outside-toplevel
        from cadquery import exporters  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as exc:
        raise SystemExit('CadQuery is required to generate geometry. Install dependencies first or use ./run.sh.') from exc

    _CADQUERY_MODULE = cadquery
    _EXPORTERS_MODULE = exporters
    return _CADQUERY_MODULE, _EXPORTERS_MODULE


def report(message, *, time_stamp=True, order=None, extra_line=False):
    """Emit progress output."""

    if order is not None:
        message = f'{order} {message}'
    if time_stamp:
        message = f'{datetime.now()}: {message}'
    if extra_line:
        message = '\n' + message
    print(message)


def remove_blanks(string):
    """Collapse whitespace for cache keys and filenames."""

    return re.sub(r'\s+', '', string)


def balanced_union(shapes):
    """Union a list of solids using a balanced tree to reduce peak intermediate size."""

    if not shapes:
        return None

    remaining_shapes = list(shapes)
    while len(remaining_shapes) > 1:
        new_shapes = []
        for index in range(0, len(remaining_shapes), 2):
            if index + 1 < len(remaining_shapes):
                new_shapes.append(remaining_shapes[index].union(remaining_shapes[index + 1]))
            else:
                new_shapes.append(remaining_shapes[index])
        remaining_shapes = new_shapes
    return remaining_shapes[0]


def format_elapsed_time(seconds_elapsed):
    """Format a runtime duration for console output."""

    if seconds_elapsed < 120:
        return f'{seconds_elapsed} seconds'
    if seconds_elapsed < 3600:
        return f'{round(seconds_elapsed / 60, 2)} minutes'
    return f'{round(seconds_elapsed / 3600, 2)} hours'


def cached_model(func):
    """Cache model-building methods in RAM and optionally on disk."""

    signature = inspect.signature(func)

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        bound_args = signature.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        order = bound_args.arguments.get('order')
        return self.cached_part(
            func.__name__,
            lambda: func(*bound_args.args, **bound_args.kwargs),
            order=order,
        )

    return wrapper


class OctahedroflakeGenerator:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Generate and export octahedroflake geometry for a single runtime config."""

    def __init__(
        self,
        config,
        *,
        base_dir=BASE_DIR,
        use_disk_cache=USE_DISK_CACHE,
        cadquery_module=None,
        exporters_module=None,
    ):
        self.config = config
        self.dimensions = calculate_dimensions(config)
        self.base_dir = Path(base_dir)
        self.use_disk_cache = use_disk_cache
        self.cq = cadquery_module
        self.exporters = exporters_module

        self.logo_stamp_path = self.base_dir / 'logo_stamp.step'
        self.part_cache_dir = self.base_dir / 'part_cache'
        self.output_root = self.base_dir / 'output'
        self.part_cache = {}

    @property
    def final_order(self):
        return self.config.iterations

    @property
    def branded(self):
        return self.config.branded

    @property
    def layer_height(self):
        return self.config.layer_height

    @property
    def nozzle_diameter(self):
        return self.config.nozzle_diameter

    @property
    def edge_size(self):
        return self.dimensions.edge_size

    @property
    def rib_width(self):
        return self.dimensions.rib_width

    @property
    def full_size(self):
        return self.dimensions.full_size

    @property
    def full_height(self):
        return self.dimensions.full_height

    @property
    def pyramid_height(self):
        return self.dimensions.pyramid_height

    @property
    def combined_height(self):
        return self.dimensions.combined_height

    @property
    def gap_height(self):
        return self.dimensions.gap_height

    def cache_key(self, part_name, order=None):
        """Build a cache key that tracks geometry-relevant parameters."""

        params = (
            f'{self.nozzle_diameter:.2f}-{self.layer_height:.2f}-'
            f'{self.edge_size:.5f}-{GAP_SIZE:.2f}-{HEIGHT_FACTOR:.4f}'
        )
        if order is not None:
            params += f'-order{order}'
        return remove_blanks(f'{params}-{part_name}')

    def output_directory(self):
        """Return the output directory for the current nozzle/layer settings."""

        return self.output_root / f'{round(self.nozzle_diameter, 2)}mm_nozzle' / f'{round(self.layer_height, 2)}mm_layer_height'

    def export_result(self, result, *, name, path, stl=False, step=False, svg=False):
        """Export a model to the requested formats."""

        path.mkdir(parents=True, exist_ok=True)
        file_stem = remove_blanks(name)

        if stl:
            self.exporters.export(result, str(path / f'{file_stem}.stl'))
        if step:
            file_path_step = path / f'{file_stem}.STEP'
            report(f'💾 {file_path_step}')
            self.exporters.export(result, str(file_path_step), self.exporters.ExportTypes.STEP)
        if svg:
            file_path_svg = path / f'{file_stem}.svg'
            report(f'💾 {file_path_svg}')
            self.exporters.export(result, str(file_path_svg))
            self.exporters.export(
                result.rotateAboutCenter((0, 0, 1), 135).rotateAboutCenter((0, 1, 0), 90),
                str(file_path_svg),
                opt={
                    "width": 1000,
                    "height": 1000,
                    "marginLeft": 100,
                    "marginTop": 100,
                    "showAxes": True,
                    "projectionDir": (0, 1, 0),
                    "strokeWidth": 0.01,
                    "strokeColor": (0, 0, 0),
                    "hiddenColor": (90, 90, 90),
                    "showHidden": True,
                },
            )

    def cached_part(self, part_name, builder, *, order=None):
        """Return a part from memory/disk cache or build and cache it."""

        cache_key = self.cache_key(part_name, order=order)
        if cache_key in self.part_cache:
            report(f'⭐️ {part_name}', order=order)
            return self.part_cache[cache_key]

        file_path = self.part_cache_dir / f'{cache_key}.STEP'
        if self.use_disk_cache and file_path.exists():
            report(f'🗃️  load from disk: {part_name}', order=order)
            part = self.cq.importers.importStep(str(file_path))
            self.part_cache[cache_key] = part
            return part

        result = builder()
        self.part_cache[cache_key] = result
        report(f'📥 RAM_Caching {part_name}', order=order)
        return result

    def save_caches_to_disk(self):
        """Persist any newly-built STEP fragments to disk."""

        if not self.use_disk_cache:
            return

        for part_name, part in self.part_cache.items():
            cache_path = self.part_cache_dir / f'{part_name}.STEP'
            if not cache_path.exists():
                self.export_result(result=part, name=part_name, path=self.part_cache_dir, step=True)

    @cached_model
    def make_single_pyramid(self, order):
        report('🔺 make a single pyramid', order=order)
        factor = 2**order
        base_size = self.edge_size * factor
        height = self.layer_height + self.pyramid_height * factor
        pyramid = (
            self.cq.Workplane('XZ').workplane(offset=-base_size / 2).moveTo(-base_size / 2, 0).lineTo(base_size / 2, 0)
            .lineTo(base_size / 2, self.layer_height).lineTo(0, height).lineTo(-base_size / 2, self.layer_height).close()
            .extrude(base_size)
        )
        return pyramid.intersect(pyramid.rotateAboutCenter((0, 0, 1), 90))

    @cached_model
    def make_ribs(self, order):
        plane = self.cq.Workplane('XY')
        report('🩻 make some ribs', order=order)
        rib = (
            plane.workplane(offset=-self.layer_height).rect(self.rib_width, self.rib_width * 2)
            .extrude(self.edge_size * (2**order) + self.layer_height).faces('<Z').workplane(20).split(keepBottom=True)
            .rotateAboutCenter((0, 0, 1), 45).rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(1, 1, 0), angleDegrees=45)
            .translate((0, 0, self.layer_height)).intersect(self.make_single_pyramid(order=order))
        )
        two_ribs = rib.union(rib.mirror(mirrorPlane='ZY'))
        return two_ribs.union(two_ribs.mirror(mirrorPlane='ZX'))

    @cached_model
    def make_logo(self):
        size = 1 if self.final_order < 3 else 2
        report('🧠 make the logo', order=self.final_order)
        factor = 2**size
        final_factor = 2**self.final_order
        z_shift_to_top = (self.pyramid_height * final_factor) - (self.pyramid_height * factor)
        if self.final_order == 1:
            z_shift = z_shift_to_top
            shift = 0
        else:
            z_shift = z_shift_to_top - (self.pyramid_height * factor)
            shift = self.edge_size / 2 * factor
        box_size = self.edge_size * (2**(size + 1))
        box = (
            self.cq.Workplane('XY').box(box_size, box_size, box_size).translate((box_size / 2, box_size / 2, 0))
            .rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(0, 0, 1), angleDegrees=-45)
        )
        move_multiplier = factor * self.edge_size / 2
        scale_multiplier = factor * self.edge_size / 2

        if not self.logo_stamp_path.exists():
            raise FileNotFoundError(f'Missing logo geometry: {self.logo_stamp_path}')

        logo = self.cq.importers.importStep(str(self.logo_stamp_path)).val().scale(scale_multiplier * 0.35)
        return (
            self.make_single_pyramid(order=size).intersect(box)
            .union(logo.translate((move_multiplier * 0.8, move_multiplier * -0.4, move_multiplier * 0.25)))
            .translate((shift, shift, z_shift))
        )

    @cached_model
    def make_gaps(self, order):
        plane = self.cq.Workplane('XY')
        report('⚔️ make the gaps', order=order)
        base_size = self.edge_size * (2**order)
        return plane.rect(base_size, GAP_SIZE).extrude(self.gap_height).union(
            plane.rect(GAP_SIZE, base_size).extrude(self.gap_height)
        )

    @cached_model
    def make_fractal_pyramid(self, order):
        if order == 0:
            return self.make_single_pyramid(0)

        factor = 2**(order - 1)
        shift = self.edge_size / 2 * factor
        height = (self.combined_height + self.layer_height) * factor
        layer_height_2 = self.layer_height * 2
        z_shift = layer_height_2 - height

        report('🥪 stack up the fractal', order=order)
        report('🥪 1/5 lower order fractal', order=order)
        lower_result = self.make_fractal_pyramid(order=order - 1)

        report('🥪 2/5 mirrored fractal', order=order)
        mirror = self.make_mirror_pyramid(order=order - 1)
        group_a = balanced_union([lower_result, mirror]).translate((0, 0, (factor - 1) * -layer_height_2))

        report('🥪 3/5 group_b - four corners', order=order)
        south = lower_result.translate((-shift, shift, z_shift))
        north = lower_result.translate((shift, -shift, z_shift))
        east = lower_result.translate((shift, shift, z_shift))
        west = lower_result.translate((-shift, -shift, z_shift))
        group_b = balanced_union([south, north, east, west])

        report('🥪 4/5 group_a + group_b', order=order)
        combined = balanced_union([group_a, group_b]).translate((0, 0, height - layer_height_2))

        report('🥪 5/5 Gaps and Ribs', order=order)
        final_result = combined.cut(self.make_gaps(order=order)).union(self.make_ribs(order=order))

        self.save_caches_to_disk()
        return final_result

    @cached_model
    def make_mirror_pyramid(self, order):
        report('🪩 make mirror', order=order)
        return self.make_fractal_pyramid(order).mirror(mirrorPlane='XY').translate((0, 0, self.layer_height))

    @cached_model
    def make_stand(self, order):
        result = self.make_fractal_pyramid(order)
        factor = 2**order
        report('🧍🏻‍♀️ make a stand', order=order)
        shift = self.edge_size / 2 * factor
        south = result.translate((-shift, shift, 0))
        north = result.translate((shift, -shift, 0))
        east = result.translate((shift, shift, 0))
        west = result.translate((-shift, -shift, 0))
        solid_base = self.cq.Workplane('XY').rect(self.edge_size * (2**(order + 1)), self.edge_size * (2**(order + 1))).extrude(0.2)

        combined_stand = balanced_union([south, north, east, west])
        full_structure = balanced_union([combined_stand, self.make_ribs(order=order + 1), solid_base])
        return full_structure.cut(self.make_gaps(order=order + 1))

    def export_pyramid(self, pyramid):
        """Export the upper pyramid half with its solid print base."""

        base_size = self.edge_size * (2**self.final_order)
        solid_base = self.cq.Workplane('XY').rect(base_size, base_size).extrude(0.2)
        pyramid_with_base = pyramid.union(solid_base)
        pyramid_name = (
            f'Sierpinski-Pyramid-{self.final_order}_{round(self.full_height / 2)}mm_for_'
            f'{round(self.layer_height, 2)}mm_layer_height_and_{round(self.nozzle_diameter, 2)}mm_nozzle'
        )
        self.export_result(pyramid_with_base, name=pyramid_name, path=self.output_directory(), stl=True)

    @cached_model
    def make_branded_pyramid(self):
        report('👷🏻‍♀️ About to make a branded pyramid', order=self.final_order)
        return self.make_fractal_pyramid(order=self.final_order).union(self.make_logo())

    @cached_model
    def make_unbranded_pyramid(self):
        report('👷🏻‍♀️ Making an unbranded pyramid', order=self.final_order)
        return self.make_fractal_pyramid(order=self.final_order)

    @cached_model
    def make_octahedron_fractal(self):
        report('💠 make it!', order=self.final_order)
        pyramid = self.make_branded_pyramid() if self.branded else self.make_unbranded_pyramid()
        self.export_pyramid(pyramid)
        mirrored = self.make_mirror_pyramid(order=self.final_order)
        self.save_caches_to_disk()
        report('🔗 combine with mirrored', order=self.final_order)
        return balanced_union([pyramid, mirrored])

    @cached_model
    def make_octahedron_fractal_with_stand(self):
        combined_model = self.make_octahedron_fractal()
        self.save_caches_to_disk()
        combined_model = combined_model.translate((0, 0, self.pyramid_height * (2**self.final_order)))

        report('🔗 combine with stand', order=self.final_order)
        return combined_model.union(self.make_stand(max(0, self.final_order - 2)))

    def run(self):
        """Generate the model, export assets, and print runtime stats."""

        start_time = timeit.default_timer()
        report('*START*', order=self.final_order, extra_line=True)
        report(f'full_size: {self.full_size}')
        report(f'full height: {self.full_height}')
        report(f'edge size: {self.edge_size}')
        flake = self.make_octahedron_fractal_with_stand()
        self.save_caches_to_disk()
        name = (
            f'Octahedroflake-{self.final_order}_{self.full_height}mm_for_'
            f'{round(self.layer_height, 2)}mm_layer_height_and_{round(self.nozzle_diameter, 2)}mm_nozzle'
        )
        self.export_result(flake, name=name, path=self.output_directory(), stl=True)
        report('DONE!')
        report(f'Elapsed time: {format_elapsed_time(round(timeit.default_timer() - start_time, 2))}')


def run(arguments=None):
    """CLI entrypoint used by both `__main__` and tests."""

    config = parse_arguments(arguments)
    cadquery_module, exporters_module = load_cadquery()
    generator = OctahedroflakeGenerator(
        config,
        cadquery_module=cadquery_module,
        exporters_module=exporters_module,
    )
    generator.run()


if __name__ == "__main__":
    run()
