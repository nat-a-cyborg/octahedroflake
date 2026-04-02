"""Unit tests for CLI parsing and lightweight generator helpers."""

# pylint: disable=duplicate-code

import contextlib
import io
import unittest
from pathlib import Path

from mesh_generator import MeshOctahedroflakeGenerator
from octahedroflake import (
    ModelConfig,
    calculate_dimensions,
    format_elapsed_time,
    parse_arguments,
)


def _ignore_report(*_args, **_kwargs):
    """Ignore progress output in tests."""


class DummyManifoldModule:  # pylint: disable=too-few-public-methods
    """Simple placeholder module for non-geometry tests."""

    class Manifold:  # pylint: disable=too-few-public-methods
        """Placeholder manifold type."""

    class Mesh:  # pylint: disable=too-few-public-methods
        """Placeholder mesh type."""


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

        expected_edge_size = (120 - 0.25) / ((2**2) * 0.7071 * 2)

        self.assertAlmostEqual(dimensions.edge_size, expected_edge_size)
        self.assertAlmostEqual(dimensions.rib_width, 1.2)
        self.assertAlmostEqual(dimensions.gap_size, 0.1)
        self.assertEqual(dimensions.full_height, 120)

    def test_nozzle_diameter_only_changes_rib_width(self):
        first = calculate_dimensions(ModelConfig(iterations=4, nozzle_diameter=0.4, desired_height=200))
        second = calculate_dimensions(ModelConfig(iterations=4, nozzle_diameter=0.6, desired_height=200))

        self.assertAlmostEqual(first.edge_size, second.edge_size)
        self.assertNotEqual(first.rib_width, second.rib_width)


class GeneratorTests(unittest.TestCase):
    """Verify generator helpers that do not require manifold operations."""

    def test_output_directory_uses_runtime_config(self):
        config = ModelConfig(iterations=3, layer_height=0.25, nozzle_diameter=0.6)
        generator = MeshOctahedroflakeGenerator(
            config,
            calculate_dimensions(config),
            base_dir=Path('/tmp/octahedroflake'),
            numpy_module=object(),
            manifold_module=DummyManifoldModule,
            reporter=_ignore_report,
            format_elapsed_time=str,
        )

        self.assertEqual(
            generator.output_directory(),
            Path('/tmp/octahedroflake/output/0.6mm_nozzle/0.25mm_layer_height'),
        )


class FormattingTests(unittest.TestCase):
    """Verify human-readable formatting helpers."""

    def test_format_elapsed_time(self):
        self.assertEqual(format_elapsed_time(12.5), '12.5 seconds')
        self.assertEqual(format_elapsed_time(180), '3.0 minutes')
        self.assertEqual(format_elapsed_time(7200), '2.0 hours')


if __name__ == '__main__':
    unittest.main()
