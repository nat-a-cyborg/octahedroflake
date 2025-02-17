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
    -h, --help              Show this help message and exit.
    -i, --iterations        Number of iterations (default: 3).
    -l, --layer-height      Layer height in mm (default: 0.2).
    -n, --nozzle-diameter   Nozzle diameter in mm (default: 0.4).
    --size-multiplier       Size multiplier (default: 0.9765625).
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
# Argument Parsing
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='octahedroflake')
iterations_default = 3
layer_height_default = 0.2
nozzle_diameter_default = 0.4
size_multiplier_default = 0.9765625

parser.add_argument('--iterations', type=int, default=iterations_default, help='number of iterations')
parser.add_argument('--layer-height', type=float, default=layer_height_default, help='layer height in mm')
parser.add_argument('--nozzle-diameter', type=float, default=nozzle_diameter_default, help='nozzle diameter in mm')
parser.add_argument('--size-multiplier', type=float, default=size_multiplier_default, help='size multiplier')

args = parser.parse_args()

NOZZLE_DIAMETER = args.nozzle_diameter
LAYER_HEIGHT = args.layer_height
FINAL_ORDER = args.iterations
SIZE_MULTIPLIER = args.size_multiplier

# -----------------------------------------------------------------------------
# Global Parameters
# -----------------------------------------------------------------------------

part_cache = {}

GAP_SIZE = 0.01
EDGE_SIZE = NOZZLE_DIAMETER * 4 * SIZE_MULTIPLIER
RIB_WIDTH = NOZZLE_DIAMETER * 2
USE_DISK_CACHE = True
HEIGHT_FACTOR = 0.7071  # see: https://www.calculatorsoup.com/calculators/geometry-solids/pyramid.php
FULL_SIZE = pow(2, FINAL_ORDER) * EDGE_SIZE
FULL_HEIGHT = math.ceil(FULL_SIZE * HEIGHT_FACTOR * 2)
PYRAMID_HEIGHT = round(EDGE_SIZE * HEIGHT_FACTOR, 2)
COMBINED_HEIGHT = PYRAMID_HEIGHT + LAYER_HEIGHT
GAP_HEIGHT = LAYER_HEIGHT + GAP_SIZE * HEIGHT_FACTOR
PART_CACHE_STEP_DIR = 'part_cache'
PART_CACHE_STL_DIR = 'parts_stl'
OUTPUT_DIR = 'output'

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

def name_for_cache(part_name, order=None):
    if order is not None:
        part_name = f'{part_name}[{order}]'
    key = f"{round(EDGE_SIZE,2)}-{round(LAYER_HEIGHT,2)}-{round(GAP_SIZE,2)}-{HEIGHT_FACTOR}-{NOZZLE_DIAMETER}-{part_name}"
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
    result = make_fractal_pyramid(order=order - 1)
    factor = 2**(order - 1)
    shift = EDGE_SIZE / 2 * factor
    height = (COMBINED_HEIGHT + LAYER_HEIGHT) * factor
    layer_height_2 = LAYER_HEIGHT * 2
    z_shift = layer_height_2 - height
    report('👯 make clones', order=order)
    mirror = result.mirror(mirrorPlane='XY').translate((0, 0, LAYER_HEIGHT))
    south = result.translate((-shift, shift, z_shift))
    north = result.translate((shift, -shift, z_shift))
    east = result.translate((shift, shift, z_shift))
    west = result.translate((-shift, -shift, z_shift))
    new_ribs = make_ribs(order=order)
    new_gaps = make_gaps(order=order)
    report('💎 combine clones and parts', order=order)
    result = (
        result.union(mirror).translate((0, 0, (factor - 1) * -layer_height_2)
                                      ).union(south).union(west).union(north).union(east).translate(
                                          (0, 0, height - layer_height_2)
                                          ).cut(new_gaps).union(new_ribs)
        )
    return result

@cache_model_decorator
def make_final_mirror():
    report('🪩 make final mirror', order=FINAL_ORDER)
    pyramid_fractal = make_fractal_pyramid(order=FINAL_ORDER)
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
    return south.union(north).union(east).union(west).cut(new_gaps).union(new_ribs).union(solid_base)

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
    report('👷🏻‍♀️ About to make an unbranded pyramid', order=FINAL_ORDER)
    fractal_pyramid = make_fractal_pyramid(order=FINAL_ORDER)
    report('👷🏻‍♀️ Finished fractaling! Now we brand and combine...', order=FINAL_ORDER)
    return fractal_pyramid

@cache_model_decorator
def make_octahedron_fractal(branded=True):
    report('💠 make it!', order=FINAL_ORDER)
    pyramid = make_branded_pyramid() if branded else make_unbranded_pyramid()
    export_pyramid(pyramid)
    mirrored = make_final_mirror()
    stand = make_stand(max(0, FINAL_ORDER - 2))
    report('🔗 combine with mirrored and stand', order=FINAL_ORDER)
    return pyramid.union(mirrored).translate((0, 0, PYRAMID_HEIGHT * (2**FINAL_ORDER))).union(stand)

def run():
    start_time = timeit.default_timer()
    report('*START*', order=FINAL_ORDER, extra_line=True)
    report(f'full_size: {FULL_SIZE}')
    report(f'full height: {FULL_HEIGHT}')
    report(f'edge size: {EDGE_SIZE}')
    flake = make_octahedron_fractal(branded=False)
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

run()
