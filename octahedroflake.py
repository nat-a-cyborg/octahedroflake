"""
octahedroflake.py

This script generates a printable 3D octahedron fractal called the "Octahedroflake,"
which is a higher-dimensional analog of the Sierpinski Triangle. The algorithm used
to create the Octahedroflake is based on the iterative subdivision of an octahedron.

For more information about an octahedron flake, see:
https://en.wikipedia.org/wiki/N-flake#Octahedron_flake

This script requires CadQuery 2.0 or later.

Usage:
    python octahedroflake.py [options]

Options:
    -h, --help          Show this help message and exit.
    -i, --iterations    Number of iterations (default: 3).
    -l, --layer-height  Layer height in mm (default: 0.2).
    -n, --nozzle-dia    Nozzle diameter in mm (default: 0.4).
    -m, --model-height  Model height in mm (default: 60).
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import timeit
from datetime import datetime
from os.path import exists
import re
import inspect
import math
import argparse
import platform
import applescript

import cadquery as cq
from cadquery import exporters

# create the argument parser
parser = argparse.ArgumentParser(description='My script description')

# add the command-line arguments
parser.add_argument('--iterations', type=int, help='the number of iterations')
parser.add_argument('--layer-height', type=float, help='the layer height in mm')
parser.add_argument('--nozzle-diameter', type=float, help='the nozzle diameter in mm')
parser.add_argument('--size-multiplier', type=float, help='how much bigger it should be from default')

# parse the command-line arguments
args = parser.parse_args()

NOZZLE_DIAMETER = args.nozzle_diameter
LAYER_HEIGHT = args.layer_height
FINAL_ORDER = args.iterations
SIZE_MULTIPLER = args.size_multiplier

part_cash = {}

GAP_SIZE = 0.01
EDGE_SIZE = NOZZLE_DIAMETER * 4 * SIZE_MULTIPLER
RIB_WIDTH = NOZZLE_DIAMETER * 2
USE_DISK_CACHE = True
HEIGHT_FACTOR = 0.7071  # https://www.calculatorsoup.com/calculators/geometry-solids/pyramid.php
FULL_SIZE = pow(2, FINAL_ORDER) * EDGE_SIZE
FULL_HEIGHT = math.ceil(FULL_SIZE * 0.7071 * 2)
PYRAMID_HEIGHT = round(EDGE_SIZE * HEIGHT_FACTOR, 2)
COMBINED_HEIGHT = PYRAMID_HEIGHT + LAYER_HEIGHT
GAP_HEIGHT = LAYER_HEIGHT + GAP_SIZE * HEIGHT_FACTOR
PART_CACHE_STEP_DIR = 'part_cache'
PART_CACHE_STL_DIR = 'parts_stl'
OUTPUT_DIR = 'output'

def report(message, *, time_stamp=True, order=None, extra_line=False):

    if order is not None:
        message = f'{str(order)} {message}'

    if time_stamp:
        date_time = datetime.now()
        message = f'{str(date_time)}: {message}'

    if extra_line:
        message = '\n' + message

    print(message)

def remove_blanks(string):
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', string)

def name_for_cache(part_name, order=None):
    if order is not None:
        part_name = f'{part_name}[{order}]'

    part_name = f'''
    {str(round(EDGE_SIZE,2))}-
    {str(round(LAYER_HEIGHT,2))}-
    {str(round(GAP_SIZE,2))}-
    {str(HEIGHT_FACTOR)}-
    {str(NOZZLE_DIAMETER)}-
    {part_name}
    '''

    part_name = remove_blanks(part_name)

    return part_name

def get_cached_model(name, order=None):
    part_name = name_for_cache(name, order=order)

    if part_name in part_cash:
        report(f'   ⭐️ {name}', order=order)
        return part_cash[part_name]

    file_path = f'{PART_CACHE_STEP_DIR}/{part_name}.STEP'
    if USE_DISK_CACHE and exists(file_path):
        report(f'   🗃️  load {name}', order=order)
        part = cq.importers.importStep(file_path)
        cache_model(part, name, order=order)
        return part

    report(f'   ❌ {name} not found in cache', order=order)
    return None

def cache_model(part, part_name, order=None):
    coded_part_name = name_for_cache(part_name, order)
    part_cash[coded_part_name] = part
    report(f"   📥 {part_name}", order=order)

def save_comments(file_path, note):
    if platform.system() == "Darwin":  # Checks if the OS is macOS
        note += f"\nNOZZLE_DIAMETER: {NOZZLE_DIAMETER}"
        note += f"\nLAYER_HEIGHT: {LAYER_HEIGHT}"
        note += f"\nFINAL_ORDER: {FINAL_ORDER}"
        note += f"\nSIZE_MULTIPLER: {SIZE_MULTIPLER}"
        applescript.tell.app("Finder", f'set comment of (POSIX file "{file_path}" as alias) to "{note}" as Unicode text')

def output(result, *, name, path, stl=False, step=False, svg=False):
    file_path = path

    if file_path != '':
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_path += '/'

    name = remove_blanks(name)
    if stl:
        file_path = file_path + name + '.stl'
        exporters.export(result, file_path)
        save_comments(file_path, name)

    if step:
        file_path = file_path + name + '.STEP'
        report(f'💾 {file_path}')
        exporters.export(result, file_path, exporters.ExportTypes.STEP)
        save_comments(file_path, name)

    if svg:
        file_path = file_path + name + '.svg'
        report(f'💾 {file_path}')
        exporters.export(result, file_path)

        exporters.export(
            result.rotateAboutCenter((0, 0, 1), 135).rotateAboutCenter((0, 1, 0), 90),
            file_path,
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

def save_caches_to_disk(clear=True):
    return
    global part_cash
    for part_name, part in part_cash.items():
        if not exists(f'{PART_CACHE_STEP_DIR}/{part_name}.STEP'):
            output(result=part, name=part_name, path=PART_CACHE_STEP_DIR, step=True)

    if clear:
        part_cash = {}  # Clear out the ram cache

def make_single_pyramid(order):
    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, order=order)
    if cached is not None:
        return cached

    report('🔺 make a single pyramid', order=order)

    factor = pow(2, order)

    base_size = EDGE_SIZE * factor

    height = LAYER_HEIGHT + PYRAMID_HEIGHT * factor

    pyramid = cq.Workplane('XZ').workplane(
        offset=-base_size / 2
        ).moveTo(-base_size / 2, 0).lineTo(base_size / 2,
                                           0).lineTo(base_size / 2,
                                                     LAYER_HEIGHT).lineTo(0,
                                                                          height).lineTo(-base_size / 2,
                                                                                         LAYER_HEIGHT).close().extrude(base_size)

    pyramid = pyramid.intersect(pyramid.rotateAboutCenter((0, 0, 1), 90))

    cache_model(pyramid, part_name, order=order)

    return pyramid

def make_ribs(order):

    plane = cq.Workplane('XY')
    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, order=order)
    if cached is not None:
        return cached

    report('🩻  make some ribs', order=order)

    rib = plane.workplane(offset=-LAYER_HEIGHT
                         ).rect(RIB_WIDTH,
                                RIB_WIDTH * 2).extrude(EDGE_SIZE * pow(2, order) + LAYER_HEIGHT).faces('<Z').workplane(20).split(
                                    keepBottom=True
                                    ).rotateAboutCenter((0, 0, 1), 45).rotate(
                                        axisStartPoint=(0, 0, 0), axisEndPoint=(1, 1, 0), angleDegrees=45
                                        ).translate((0, 0, LAYER_HEIGHT)).intersect(make_single_pyramid(order=order))

    two_ribs = rib.union(rib.mirror(mirrorPlane='ZY'))
    four_ribs = two_ribs.union(two_ribs.mirror(mirrorPlane='ZX'))

    cache_model(four_ribs, part_name, order=order)
    return four_ribs

def make_logo():
    size = 1 if FINAL_ORDER < 3 else 2
    part_name = inspect.currentframe().f_code.co_name
    part_name = f'{part_name}[{size}]'

    cached = get_cached_model(part_name, order=FINAL_ORDER)
    if cached is not None:
        return cached

    report('🧠 make the logo', order=FINAL_ORDER)

    factor = pow(2, size)
    final_factor = pow(2, FINAL_ORDER)

    z_shift_to_top = (PYRAMID_HEIGHT * final_factor) - (PYRAMID_HEIGHT * factor)

    if FINAL_ORDER == 1:
        z_shift = z_shift_to_top
        shift = 0
    else:
        z_shift = z_shift_to_top - (PYRAMID_HEIGHT * factor)

        shift = EDGE_SIZE / 2 * factor

    box_size = EDGE_SIZE * pow(2, size + 1)

    box = (
        cq.Workplane('XY').box(box_size, box_size, box_size).translate(
            (box_size / 2, box_size / 2, 0)
            ).rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(0, 0, 1), angleDegrees=-45)
        )

    move_multiplier = factor * EDGE_SIZE / 2
    scale_multiplier = factor * EDGE_SIZE / 2

    logo = cq.importers.importStep("logo_stamp.step").val().scale(scale_multiplier * 0.35)

    result = (
        make_single_pyramid(order=size).intersect(box).union(
            logo.translate((move_multiplier * 0.8, move_multiplier * -0.4, move_multiplier * 0.25))
            ).translate((shift, shift, z_shift))
        )

    cache_model(result, part_name, order=FINAL_ORDER)
    return result

def make_gaps(order):
    plane = cq.Workplane('XY')

    part_name = inspect.currentframe().f_code.co_name
    cached = get_cached_model(part_name, order)
    if cached is not None:
        return cached

    report('⚔️  make the gaps', order=order)

    base_size = EDGE_SIZE * pow(2, order)

    gaps = plane.rect(base_size, GAP_SIZE).extrude(GAP_HEIGHT).union(plane.rect(GAP_SIZE, base_size).extrude(GAP_HEIGHT))

    cache_model(gaps, part_name, order)
    return gaps

def make_fractal_pyramid(order):
    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, order)
    if cached is not None:
        return cached

    if order == 0:
        result = make_single_pyramid(0)
        cache_model(result, part_name, order=order)
        return result

    result = make_fractal_pyramid(order=order - 1)

    save_caches_to_disk()

    factor = pow(2, order - 1)
    shift = EDGE_SIZE / 2 * factor
    height = (COMBINED_HEIGHT + LAYER_HEIGHT) * factor
    layer_height_2 = LAYER_HEIGHT * 2
    z_shift = (layer_height_2) - height

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

    cache_model(result, part_name, order=order)
    return result

def make_final_mirror():
    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, order=FINAL_ORDER)
    if cached is not None:
        return cached
    report('🪩  make final mirror', order=FINAL_ORDER)
    pyramid_fractal = make_fractal_pyramid(order=FINAL_ORDER)
    mirrored = pyramid_fractal.mirror(mirrorPlane='XY').translate((0, 0, LAYER_HEIGHT))
    cache_model(mirrored, part_name, order=FINAL_ORDER)
    return mirrored

def make_stand(order):
    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, order)
    if cached is not None:
        return cached

    cached_pyramid = make_fractal_pyramid(order)
    if cached_pyramid is not None:
        result = cached_pyramid

    factor = pow(2, order)
    base_size = EDGE_SIZE * factor

    report('🧍🏻‍♀️ make a stand', order=order)

    factor = pow(2, order)
    shift = EDGE_SIZE / 2 * factor
    south = result.translate((-shift, shift, 0))
    north = result.translate((shift, -shift, 0))
    east = result.translate((shift, shift, 0))
    west = result.translate((-shift, -shift, 0))
    new_gaps = make_gaps(order=order + 1)
    new_ribs = make_ribs(order=order + 1)

    base_size = EDGE_SIZE * pow(2, order + 1)

    solid_base = cq.Workplane('XY').rect(base_size, base_size).extrude(0.2)
    stand = north.union(east).union(south).union(west).cut(new_gaps).union(new_ribs).union(solid_base)

    cache_model(stand, part_name, order=order)
    return stand

def export_pyramid():
    base_size = EDGE_SIZE * pow(2, FINAL_ORDER)
    solid_base = cq.Workplane('XY').rect(base_size, base_size).extrude(0.2)
    pyramid_with_base = make_branded_pyramid().union(solid_base)

    pyramid_name = (
        f'Sierpinski-Pyramid-{FINAL_ORDER}_{round(FULL_HEIGHT/2)}mm_for_{round(LAYER_HEIGHT, 2)}mm_layer_height_and_{round(NOZZLE_DIAMETER, 2)}mm_nozzle'
        )
    directory = f'{OUTPUT_DIR}/{round(NOZZLE_DIAMETER, 2)}mm_nozzle/{round(LAYER_HEIGHT, 2)}mm_layer_height/'
    pyramid_name = remove_blanks(pyramid_name)
    output(pyramid_with_base, name=pyramid_name, path=directory, stl=True)

def make_branded_pyramid():

    report('👷🏻‍♀️ About to make a branded pyramid', order=FINAL_ORDER)

    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, FINAL_ORDER)
    if cached is not None:
        return cached

    branded_pyramid = make_fractal_pyramid(order=FINAL_ORDER).union(make_logo())
    cache_model(branded_pyramid, part_name, order=FINAL_ORDER)
    return branded_pyramid

def make_unbranded_pyramid():
    report('👷🏻‍♀️ About to make an unbranded pyramid', order=FINAL_ORDER)

    part_name = inspect.currentframe().f_code.co_name

    cached = get_cached_model(part_name, FINAL_ORDER)
    if cached is not None:
        return cached

    fractal_pyramid = make_fractal_pyramid(order=FINAL_ORDER)

    report('👷🏻‍♀️ finished fractaling! now we brand and combine...', order=FINAL_ORDER)

    save_caches_to_disk(clear=False)

    cache_model(fractal_pyramid, part_name, order=FINAL_ORDER)
    return fractal_pyramid

def make_octahedron_fractal(branded=True):
    part_name = inspect.currentframe().f_code.co_name
    part_name = f'{part_name}-'

    cached = get_cached_model(part_name, order=FINAL_ORDER)
    if cached is not None:
        return cached

    report('💠  make it!', order=FINAL_ORDER)

    save_caches_to_disk()
    stand = None

    if branded:
        pyramid = make_branded_pyramid()
    else:
        pyramid = make_unbranded_pyramid()

    export_pyramid()
    mirrored = make_final_mirror()
    stand = make_stand(max(0, FINAL_ORDER - 2))
    save_caches_to_disk()

    report('🔗 combine with mirrored and stand', order=FINAL_ORDER)

    result = (pyramid.union(mirrored).translate((0, 0, PYRAMID_HEIGHT * pow(2, FINAL_ORDER))).union(stand))

    cache_model(result, part_name, order=FINAL_ORDER)
    return result

def run():

    start_time = timeit.default_timer()
    report('*START*', order=FINAL_ORDER, extra_line=True)
    report(f'full_size: {str(FULL_SIZE)}')
    report(f'full height: {str(FULL_HEIGHT)}')
    report(f'edge size: {EDGE_SIZE}')

    flake = make_octahedron_fractal()  # .rotateAboutCenter((0, 0, 1), 45)
    save_caches_to_disk()

    name = f'''Octahedroflake-{FINAL_ORDER}_{FULL_HEIGHT}mm_for_{str(round(LAYER_HEIGHT,2))}mm_layer_height_and_{str(round(NOZZLE_DIAMETER,2))}mm_nozzle'''
    name = remove_blanks(name)

    directory = f'{OUTPUT_DIR}/{round(NOZZLE_DIAMETER,2)}mm_nozzle/{round(LAYER_HEIGHT,2)}mm_layer_height/'
    output(flake, name=name, path=directory, stl=True)

    report('DONE!')

    seconds_elapsed = round(timeit.default_timer() - start_time, 2)

    if seconds_elapsed < 120:
        report(f"Elapsed time: {seconds_elapsed} seconds")
    elif seconds_elapsed < 3600:
        report(f"Elapsed time: {round(seconds_elapsed/60,2)} minutes")
    else:
        report(f"Elapsed time: {round(seconds_elapsed/60/60,2)} hours")

run()
