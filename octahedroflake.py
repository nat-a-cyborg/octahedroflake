#!/usr/bin/env python3
"""
octahedroflake.py

This script generates a printable 3D octahedron fractal called the "Octahedroflake,"
a higher-dimensional analog of the Sierpinski Triangle. The algorithm is based on
iterative subdivision of an octahedron.

For more information about an octahedron flake, see:
https://en.wikipedia.org/wiki/N-flake#Octahedron_flake

Requires CadQuery 2.0 or later.

Usage:
    python octahedroflake.py [options]

Options:
    -h, --help                Show this help message and exit.
    -i, --iterations          Number of iterations (default: 4).
    -l, --layer-height        Layer height in mm (default: 0.2).
    -n, --nozzle-diameter     Nozzle diameter in mm (default: 0.4).
    --desired_height_default  The Desired height of the model (default: 200).
    --branded                 Include branding in the model.
"""

import os
import timeit
from datetime import datetime
from os.path import exists
import re
import inspect
import math
import argparse

import cadquery as cq
from cadquery import exporters

# -----------------------------------------------------------------------------
# Parameter Setup: Either from interactive form cell or command-line arguments
# -----------------------------------------------------------------------------

ITERATIONS_DEFAULT = 4
LAYER_HEIGHT_DEFAULT = 0.2
NOZZLE_DIAMETER_DEFAULT = 0.4
DESIRED_HEIGHT_DEFAULT = 200
BRANDED_DEFAULT = False

parser = argparse.ArgumentParser(description='octahedroflake')
parser.add_argument('-i', '--iterations', type=int, default=ITERATIONS_DEFAULT, help='number of iterations')
parser.add_argument('-l', '--layer-height', type=float, default=LAYER_HEIGHT_DEFAULT, help='layer height in mm')
parser.add_argument('-n', '--nozzle-diameter', type=float, default=NOZZLE_DIAMETER_DEFAULT, help='nozzle diameter in mm')
parser.add_argument('--desired_height', type=float, default=DESIRED_HEIGHT_DEFAULT, help='desired height')

group = parser.add_mutually_exclusive_group()
group.add_argument('--branded', dest='branded', action='store_true', help='Include branding in the model (default)')
parser.set_defaults(branded=BRANDED_DEFAULT)

# Use parse_known_args to ignore extra args (e.g. Colab's -f flag)
args, unknown = parser.parse_known_args()

BRANDED = args.branded
NOZZLE_DIAMETER = args.nozzle_diameter
LAYER_HEIGHT = args.layer_height
FINAL_ORDER = args.iterations
HEIGHT_FACTOR = 0.7071  # see: https://www.calculatorsoup.com/calculators/geometry-solids/pyramid.php

# -----------------------------------------------------------------------------
# Compute EDGE_SIZE directly from desired height
# -----------------------------------------------------------------------------
EDGE_SIZE = args.desired_height / ((2**FINAL_ORDER) * (NOZZLE_DIAMETER * 4) * HEIGHT_FACTOR * 2)

GAP_SIZE = 0.01
RIB_WIDTH = NOZZLE_DIAMETER * 2
USE_DISK_CACHE = True

FULL_SIZE = pow(2, FINAL_ORDER) * EDGE_SIZE
FULL_HEIGHT = math.ceil(FULL_SIZE * HEIGHT_FACTOR * 2)
PYRAMID_HEIGHT = round(EDGE_SIZE * HEIGHT_FACTOR, 2)
COMBINED_HEIGHT = PYRAMID_HEIGHT + LAYER_HEIGHT
GAP_HEIGHT = LAYER_HEIGHT + GAP_SIZE * HEIGHT_FACTOR

PART_CACHE_STEP_DIR = 'part_cache'
PART_CACHE_STL_DIR = 'parts_stl'
OUTPUT_DIR = 'output'

part_cache = {}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def report(message, *, time_stamp=True, order=None, extra_line=False):
    if order is not None:
        message = f'{order} {message}'
    if time_stamp:
        message = f'{datetime.now()}: {message}'
    if extra_line:
        message = '\n' + message
    print(message)

def remove_blanks(string):
    return re.sub(r'\s+', '', string)

def balanced_union(shapes):
    """
    Perform a union on a list of shapes using a balanced binary tree approach.
    This can reduce the size of intermediate geometry compounds and help limit peak memory usage.
    """
    if not shapes:
        return None
    while len(shapes) > 1:
        new_shapes = []
        for i in range(0, len(shapes), 2):
            if i + 1 < len(shapes):
                new_shapes.append(shapes[i].union(shapes[i + 1]))
            else:
                new_shapes.append(shapes[i])
        shapes = new_shapes
    return shapes[0]

def name_for_cache(part_name, order=None):
    # Include key parameters that influence the model
    # (removed SIZE_MULTIPLIER and replaced with EDGE_SIZE)
    params = f"{NOZZLE_DIAMETER:.2f}-{LAYER_HEIGHT:.2f}-{EDGE_SIZE:.5f}-{GAP_SIZE:.2f}-{HEIGHT_FACTOR:.4f}"
    if order is not None:
        params += f"-order{order}"
    key = f"{params}-{part_name}"
    return remove_blanks(key)

def cache_model(part, part_name, order=None):
    coded_part_name = name_for_cache(part_name, order)
    part_cache[coded_part_name] = part
    report(f"📥 RAM_Caching {part_name}", order=order)

def output(result, *, name, path, stl=False, step=False, svg=False):
    if path and not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '/' if path else ''
    name = remove_blanks(name)
    if stl:
        exporters.export(result, file_path + name + '.stl')
    if step:
        file_path_step = file_path + name + '.STEP'
        report(f'💾 {file_path_step}')
        exporters.export(result, file_path_step, exporters.ExportTypes.STEP)
    if svg:
        file_path_svg = file_path + name + '.svg'
        report(f'💾 {file_path_svg}')
        exporters.export(result, file_path_svg)
        exporters.export(
            result.rotateAboutCenter((0, 0, 1), 135).rotateAboutCenter((0, 1, 0), 90),
            file_path_svg,
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
                }
            )

def save_caches_to_disk():
    if USE_DISK_CACHE:
        for part_name, part in part_cache.items():
            if not exists(f'{PART_CACHE_STEP_DIR}/{part_name}.STEP'):
                output(result=part, name=part_name, path=PART_CACHE_STEP_DIR, step=True)

def cache_model_decorator(func):
    def wrapper(*args, **kwargs):
        part_name = func.__name__
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        order = bound_args.arguments.get('order', None)
        cache_key = name_for_cache(part_name, order=order)
        if cache_key in part_cache:
            report(f'⭐️ {part_name}', order=order)
            return part_cache[cache_key]
        file_path = os.path.join(PART_CACHE_STEP_DIR, f"{cache_key}.STEP")
        if USE_DISK_CACHE and exists(file_path):
            report(f'🗃️  load from disk: {part_name}', order=order)
            part = cq.importers.importStep(file_path)
            part_cache[cache_key] = part
            return part
        result = func(*args, **kwargs)
        cache_model(result, part_name, order=order)
        return result

    return wrapper

# -----------------------------------------------------------------------------
# Model Generation Functions
# -----------------------------------------------------------------------------

@cache_model_decorator
def make_single_pyramid(order):
    report('🔺 make a single pyramid', order=order)
    factor = 2**order
    base_size = EDGE_SIZE * factor
    height = LAYER_HEIGHT + PYRAMID_HEIGHT * factor
    pyramid = (
        cq.Workplane('XZ').workplane(
            offset=-base_size / 2
            ).moveTo(-base_size / 2,
                     0).lineTo(base_size / 2,
                               0).lineTo(base_size / 2,
                                         LAYER_HEIGHT).lineTo(0, height).lineTo(-base_size / 2,
                                                                                LAYER_HEIGHT).close().extrude(base_size)
        )
    return pyramid.intersect(pyramid.rotateAboutCenter((0, 0, 1), 90))

@cache_model_decorator
def make_ribs(order):
    plane = cq.Workplane('XY')
    report('🩻 make some ribs', order=order)
    rib = (
        plane.workplane(
            offset=-LAYER_HEIGHT
            ).rect(RIB_WIDTH, RIB_WIDTH * 2).extrude(EDGE_SIZE * (2**order) + LAYER_HEIGHT).faces('<Z').workplane(20).split(
                keepBottom=True
                ).rotateAboutCenter((0, 0, 1), 45).rotate(axisStartPoint=(0, 0, 0),
                                                          axisEndPoint=(1, 1, 0), angleDegrees=45).translate(
                                                              (0, 0, LAYER_HEIGHT)
                                                              ).intersect(make_single_pyramid(order=order))
        )
    two_ribs = rib.union(rib.mirror(mirrorPlane='ZY'))
    return two_ribs.union(two_ribs.mirror(mirrorPlane='ZX'))

@cache_model_decorator
def make_logo():
    size = 1 if FINAL_ORDER < 3 else 2
    report('🧠 make the logo', order=FINAL_ORDER)
    factor = 2**size
    final_factor = 2**FINAL_ORDER
    z_shift_to_top = (PYRAMID_HEIGHT * final_factor) - (PYRAMID_HEIGHT * factor)
    if FINAL_ORDER == 1:
        z_shift, shift = z_shift_to_top, 0
    else:
        z_shift = z_shift_to_top - (PYRAMID_HEIGHT * factor)
        shift = EDGE_SIZE / 2 * factor
    box_size = EDGE_SIZE * (2**(size + 1))
    box = (
        cq.Workplane('XY').box(box_size, box_size, box_size).translate(
            (box_size / 2, box_size / 2, 0)
            ).rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(0, 0, 1), angleDegrees=-45)
        )
    move_multiplier = factor * EDGE_SIZE / 2
    scale_multiplier = factor * EDGE_SIZE / 2
    logo = cq.importers.importStep("logo_stamp.step").val().scale(scale_multiplier * 0.35)
    return (
        make_single_pyramid(order=size).intersect(box).union(
            logo.translate((move_multiplier * 0.8, move_multiplier * -0.4, move_multiplier * 0.25))
            ).translate((shift, shift, z_shift))
        )

@cache_model_decorator
def make_gaps(order):
    plane = cq.Workplane('XY')
    report('⚔️ make the gaps', order=order)
    base_size = EDGE_SIZE * (2**order)
    gaps = (plane.rect(base_size, GAP_SIZE).extrude(GAP_HEIGHT).union(plane.rect(GAP_SIZE, base_size).extrude(GAP_HEIGHT)))
    return gaps

@cache_model_decorator
def make_fractal_pyramid(order):
    if order == 0:
        return make_single_pyramid(0)

    factor = 2**(order - 1)
    shift = EDGE_SIZE / 2 * factor
    height = (COMBINED_HEIGHT + LAYER_HEIGHT) * factor
    layer_height_2 = LAYER_HEIGHT * 2
    z_shift = layer_height_2 - height

    report('🥪 stack up the fractal', order=order)
    report('🥪 1/5 lower order fractal', order=order)
    # Compute the lower order fractal
    lower_result = make_fractal_pyramid(order=order - 1)

    # Group the parts into two balanced unions
    report('🥪 2/5 mirrored fractal', order=order)
    mirror = make_mirror_pyramid(order=order - 1)
    group_a = balanced_union([lower_result, mirror]).translate((0, 0, (factor - 1) * -layer_height_2))

    report('🥪 3/5 group_b - four corners', order=order)
    south = lower_result.translate((-shift, shift, z_shift))
    north = lower_result.translate((shift, -shift, z_shift))
    east = lower_result.translate((shift, shift, z_shift))
    west = lower_result.translate((-shift, -shift, z_shift))
    group_b = balanced_union([south, north, east, west])

    # Combine both groups and apply the final translation
    report('🥪 4/5 group_a + group_b', order=order)
    combined = balanced_union([group_a, group_b]).translate((0, 0, height - layer_height_2))

    report('🥪 5/5 Gaps and Ribs', order=order)
    new_gaps = make_gaps(order=order)
    new_ribs = make_ribs(order=order)
    final_result = combined.cut(new_gaps).union(new_ribs)

    save_caches_to_disk()
    return final_result

@cache_model_decorator
def make_mirror_pyramid(order):
    report('🪩 make mirror', order=order)
    pyramid_fractal = make_fractal_pyramid(order)
    return pyramid_fractal.mirror(mirrorPlane='XY').translate((0, 0, LAYER_HEIGHT))

@cache_model_decorator
def make_stand(order):
    result = make_fractal_pyramid(order)
    factor = 2**order
    report('🧍🏻‍♀️ make a stand', order=order)
    shift = EDGE_SIZE / 2 * factor
    south = result.translate((-shift, shift, 0))
    north = result.translate((shift, -shift, 0))
    east = result.translate((shift, shift, 0))
    west = result.translate((-shift, -shift, 0))
    new_gaps = make_gaps(order=order + 1)
    new_ribs = make_ribs(order=order + 1)
    base_size = EDGE_SIZE * (2**(order + 1))
    solid_base = cq.Workplane('XY').rect(base_size, base_size).extrude(0.2)

    combined_stand = balanced_union([south, north, east, west])
    full_structure = balanced_union([combined_stand, new_ribs, solid_base])
    final_stand = full_structure.cut(new_gaps)
    return final_stand

def export_pyramid(pyramid):
    base_size = EDGE_SIZE * (2**FINAL_ORDER)
    solid_base = cq.Workplane('XY').rect(base_size, base_size).extrude(0.2)
    pyramid_with_base = pyramid.union(solid_base)
    pyramid_name = f'Sierpinski-Pyramid-{FINAL_ORDER}_{round(FULL_HEIGHT/2)}mm_for_{round(LAYER_HEIGHT,2)}mm_layer_height_and_{round(NOZZLE_DIAMETER,2)}mm_nozzle'
    directory = f'{OUTPUT_DIR}/{round(NOZZLE_DIAMETER,2)}mm_nozzle/{round(LAYER_HEIGHT,2)}mm_layer_height/'
    output(pyramid_with_base, name=remove_blanks(pyramid_name), path=directory, stl=True)

@cache_model_decorator
def make_branded_pyramid():
    report('👷🏻‍♀️ About to make a branded pyramid', order=FINAL_ORDER)
    return make_fractal_pyramid(order=FINAL_ORDER).union(make_logo())

@cache_model_decorator
def make_unbranded_pyramid():
    report('👷🏻‍♀️ Making an unbranded pyramid', order=FINAL_ORDER)
    fractal_pyramid = make_fractal_pyramid(order=FINAL_ORDER)
    return fractal_pyramid

@cache_model_decorator
def make_octahedron_fractal():
    report('💠 make it!', order=FINAL_ORDER)
    pyramid = make_branded_pyramid() if BRANDED else make_unbranded_pyramid()
    export_pyramid(pyramid)
    mirrored = make_mirror_pyramid(order=FINAL_ORDER)
    save_caches_to_disk()
    report('🔗 combine with mirrored', order=FINAL_ORDER)

    combined_model = balanced_union([pyramid, mirrored])

    return combined_model

@cache_model_decorator
def make_octahedron_fractal_with_stand():
    combined_model = make_octahedron_fractal()
    save_caches_to_disk()
    combined_model = combined_model.translate((0, 0, PYRAMID_HEIGHT * (2**FINAL_ORDER)))

    report('🔗 combine with stand', order=FINAL_ORDER)
    stand = make_stand(max(0, FINAL_ORDER - 2))
    combined_model = combined_model.union(stand)
    return combined_model

def run():
    start_time = timeit.default_timer()
    report('*START*', order=FINAL_ORDER, extra_line=True)
    report(f'full_size: {FULL_SIZE}')
    report(f'full height: {FULL_HEIGHT}')
    report(f'edge size: {EDGE_SIZE}')
    flake = make_octahedron_fractal_with_stand()
    save_caches_to_disk()
    name = f'Octahedroflake-{FINAL_ORDER}_{FULL_HEIGHT}mm_for_{round(LAYER_HEIGHT,2)}mm_layer_height_and_{round(NOZZLE_DIAMETER,2)}mm_nozzle'
    directory = f'{OUTPUT_DIR}/{round(NOZZLE_DIAMETER,2)}mm_nozzle/{round(LAYER_HEIGHT,2)}mm_layer_height/'
    output(flake, name=remove_blanks(name), path=directory, stl=True)
    report('DONE!')
    seconds_elapsed = round(timeit.default_timer() - start_time, 2)
    if seconds_elapsed < 120:
        report(f"Elapsed time: {seconds_elapsed} seconds")
    elif seconds_elapsed < 3600:
        report(f"Elapsed time: {round(seconds_elapsed/60,2)} minutes")
    else:
        report(f"Elapsed time: {round(seconds_elapsed/3600,2)} hours")

if __name__ == "__main__":
    run()
