"""Unit tests for CLI parsing and lightweight generator helpers."""

import contextlib
import io
import unittest
from pathlib import Path

from octahedroflake import (
    ModelConfig,
    OctahedroflakeGenerator,
    calculate_dimensions,
    format_elapsed_time,
    parse_arguments,
)


class ParseArgumentsTests(unittest.TestCase):
    """Verify CLI parsing behavior."""

    def test_defaults(self):
        self.assertEqual(parse_arguments([]), ModelConfig())

    def test_ignores_unknown_arguments(self):
        config = parse_arguments(['--iterations', '3', '--desired_height', '150', '-f', 'ignored'])

        self.assertEqual(config.iterations, 3)
        self.assertEqual(config.desired_height, 150)

    def test_rejects_non_positive_values(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(['--desired_height', '0'])


class DimensionTests(unittest.TestCase):
    """Verify dimension calculations."""

    def test_calculate_dimensions(self):
        config = ModelConfig(iterations=2, layer_height=0.25, nozzle_diameter=0.6, desired_height=120)
        dimensions = calculate_dimensions(config)

        expected_edge_size = 120 / ((2**2) * (0.6 * 4) * 0.7071 * 2)

        self.assertAlmostEqual(dimensions.edge_size, expected_edge_size)
        self.assertAlmostEqual(dimensions.rib_width, 1.2)
        self.assertEqual(dimensions.full_height, 50)


class GeneratorTests(unittest.TestCase):
    """Verify generator helpers that do not require CadQuery."""

    def test_output_directory_uses_runtime_config(self):
        generator = OctahedroflakeGenerator(
            ModelConfig(iterations=3, layer_height=0.25, nozzle_diameter=0.6),
            base_dir=Path('/tmp/octahedroflake'),
        )

        self.assertEqual(
            generator.output_directory(),
            Path('/tmp/octahedroflake/output/0.6mm_nozzle/0.25mm_layer_height'),
        )

    def test_cache_key_changes_with_runtime_parameters(self):
        first = OctahedroflakeGenerator(ModelConfig(iterations=3, nozzle_diameter=0.4))
        second = OctahedroflakeGenerator(ModelConfig(iterations=3, nozzle_diameter=0.6))

        self.assertNotEqual(first.cache_key('make_ribs', order=2), second.cache_key('make_ribs', order=2))


class FormattingTests(unittest.TestCase):
    """Verify human-readable formatting helpers."""

    def test_format_elapsed_time(self):
        self.assertEqual(format_elapsed_time(12.5), '12.5 seconds')
        self.assertEqual(format_elapsed_time(180), '3.0 minutes')
        self.assertEqual(format_elapsed_time(7200), '2.0 hours')


if __name__ == '__main__':
    unittest.main()
