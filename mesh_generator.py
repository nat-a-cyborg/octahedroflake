"""Direct STL mesh generator for Octahedroflake models."""

import math
import struct
import timeit
from pathlib import Path

BASE_PLATE_THICKNESS = 0.2


def _remove_blanks(string):
    """Collapse whitespace for filenames."""

    return ''.join(string.split())


class MeshOctahedroflakeGenerator:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Generate Octahedroflake STL geometry without a CAD kernel."""

    def __init__(self, config, dimensions, *, base_dir, numpy_module, manifold_module, reporter, format_elapsed_time):
        self.config = config
        self.dimensions = dimensions
        self.base_dir = Path(base_dir)
        self.output_root = self.base_dir / 'output'
        self.np = numpy_module
        self.manifold_cls = manifold_module.Manifold
        self.mesh_cls = manifold_module.Mesh
        self.report = reporter
        self.format_elapsed_time = format_elapsed_time

        if self.config.branded:
            raise SystemExit('Branding is not supported in the mesh-only generator yet.')

    def output_directory(self):
        """Return the output directory for the current nozzle/layer settings."""

        return (
            self.output_root
            / f'{round(self.config.nozzle_diameter, 2)}mm_nozzle'
            / f'{round(self.config.layer_height, 2)}mm_layer_height'
        )

    def manifold_from_vertices_faces(self, vertices, faces):
        """Construct a Manifold from explicit vertices and triangle indices."""

        return self.manifold_cls(
            self.mesh_cls(
                self.np.array(vertices, dtype=self.np.float32),
                self.np.array(faces, dtype=self.np.uint32),
            )
        )

    def rotation_matrix(self, axis, angle_degrees):
        """Return a 3x3 rotation matrix for an axis-angle transform."""

        angle = math.radians(angle_degrees)
        axis = self.np.array(axis, dtype=float)
        axis = axis / self.np.linalg.norm(axis)
        x, y, z = axis
        cosine = math.cos(angle)
        sine = math.sin(angle)
        complement = 1 - cosine
        return self.np.array(
            [
                [
                    x * x * complement + cosine,
                    x * y * complement - z * sine,
                    x * z * complement + y * sine,
                ],
                [
                    y * x * complement + z * sine,
                    y * y * complement + cosine,
                    y * z * complement - x * sine,
                ],
                [
                    z * x * complement - y * sine,
                    z * y * complement + x * sine,
                    z * z * complement + cosine,
                ],
            ],
            dtype=float,
        )

    def transform(self, manifold, matrix, translate=(0, 0, 0)):
        """Apply an affine transform to a mesh manifold."""

        affine = self.np.concatenate([matrix, self.np.array(translate, dtype=float).reshape(3, 1)], axis=1)
        return manifold.transform(affine.tolist())

    def write_binary_stl(self, *, manifold, name, file_path):
        """Write a manifold mesh to a binary STL file."""

        mesh = manifold.to_mesh()
        vertices = self.np.asarray(mesh.vert_properties[:, :3], dtype=self.np.float32)
        faces = self.np.asarray(mesh.tri_verts, dtype=self.np.uint32)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        header = _remove_blanks(name).encode('ascii', 'ignore')[:80].ljust(80, b' ')

        with file_path.open('wb') as output_file:
            output_file.write(header)
            output_file.write(struct.pack('<I', len(faces)))

            for triangle in faces:
                vertex_a, vertex_b, vertex_c = vertices[triangle]
                normal = self.np.cross(vertex_b - vertex_a, vertex_c - vertex_a)
                magnitude = self.np.linalg.norm(normal)
                if magnitude:
                    normal = normal / magnitude
                else:
                    normal = self.np.zeros(3, dtype=self.np.float32)

                output_file.write(
                    struct.pack(
                        '<12fH',
                        *normal.tolist(),
                        *vertex_a.tolist(),
                        *vertex_b.tolist(),
                        *vertex_c.tolist(),
                        0,
                    )
                )

    def export_result(self, result, *, name, path):
        """Export a mesh result as STL."""

        file_path = path / f'{_remove_blanks(name)}.stl'
        self.report(f'💾 {file_path}')
        self.write_binary_stl(manifold=result, name=name, file_path=file_path)

    def make_base_plate(self, size):
        """Build a thin square plate used to stabilize printed output."""

        return self.manifold_cls.cube((size, size, BASE_PLATE_THICKNESS), center=True).translate(
            (0, 0, BASE_PLATE_THICKNESS / 2)
        )

    def pyramid_name(self):
        """Return the filename stem for the upper pyramid export."""

        return (
            f'Sierpinski-Pyramid-{self.config.iterations}_{round(self.dimensions.full_height / 2)}mm_for_'
            f'{round(self.config.layer_height, 2)}mm_layer_height_and_{round(self.config.nozzle_diameter, 2)}mm_nozzle'
        )

    def model_name(self):
        """Return the filename stem for the full octahedroflake export."""

        return (
            f'Octahedroflake-{self.config.iterations}_{self.dimensions.full_height}mm_for_'
            f'{round(self.config.layer_height, 2)}mm_layer_height_and_{round(self.config.nozzle_diameter, 2)}mm_nozzle'
        )

    def make_single_pyramid(self, order):
        """Build the basic square prism + pyramid unit for a given order."""

        factor = 2**order
        base_size = self.dimensions.edge_size * factor
        shoulder_z = self.config.layer_height
        apex_z = self.config.layer_height + self.dimensions.pyramid_height * factor
        half = base_size / 2

        return self.manifold_from_vertices_faces(
            [
                (-half, -half, 0),
                (half, -half, 0),
                (half, half, 0),
                (-half, half, 0),
                (-half, -half, shoulder_z),
                (half, -half, shoulder_z),
                (half, half, shoulder_z),
                (-half, half, shoulder_z),
                (0, 0, apex_z),
            ],
            [
                (0, 2, 1),
                (0, 3, 2),
                (0, 1, 5),
                (0, 5, 4),
                (1, 2, 6),
                (1, 6, 5),
                (2, 3, 7),
                (2, 7, 6),
                (3, 0, 4),
                (3, 4, 7),
                (4, 5, 8),
                (5, 6, 8),
                (6, 7, 8),
                (7, 4, 8),
            ],
        )

    def make_gaps(self, order):
        """Build the cross-shaped slot removed at each recursive level."""

        base_size = self.dimensions.edge_size * (2**order)
        z_shift = self.dimensions.gap_height / 2
        return (
            self.manifold_cls.cube(
                (base_size, self.dimensions.gap_size, self.dimensions.gap_height),
                center=True,
            ).translate((0, 0, z_shift))
            + self.manifold_cls.cube(
                (self.dimensions.gap_size, base_size, self.dimensions.gap_height),
                center=True,
            ).translate((0, 0, z_shift))
        )

    def make_ribs(self, order):
        """Build the diagonal reinforcing ribs for a recursive cell."""

        factor = 2**order
        length = self.dimensions.edge_size * factor + self.config.layer_height
        rib = self.manifold_cls.cube((self.dimensions.rib_width, self.dimensions.rib_width * 2, length), center=True)
        rib = rib.translate((0, 0, (self.dimensions.edge_size * factor - self.config.layer_height) / 2))
        rib = rib.rotate((0, 0, 45))
        rib = self.transform(rib, self.rotation_matrix((1, 1, 0), 45))
        rib = rib.translate((0, 0, self.config.layer_height)) ^ self.make_single_pyramid(order)

        two_ribs = rib + rib.mirror((1, 0, 0))
        return two_ribs + two_ribs.mirror((0, 1, 0))

    def make_fractal_pyramid(self, order):
        """Recursively build the upper pyramid half as a triangle mesh manifold."""

        if order == 0:
            return self.make_single_pyramid(0)

        factor = 2**(order - 1)
        shift = self.dimensions.edge_size / 2 * factor
        height = (self.dimensions.combined_height + self.config.layer_height) * factor
        layer_height_2 = self.config.layer_height * 2
        z_shift = layer_height_2 - height

        self.report('🥪 stack up the fractal', order=order)
        lower_result = self.make_fractal_pyramid(order - 1)
        mirror = lower_result.mirror((0, 0, 1)).translate((0, 0, self.config.layer_height))
        group_a = (lower_result + mirror).translate((0, 0, (factor - 1) * -layer_height_2))

        group_b = (
            lower_result.translate((-shift, shift, z_shift))
            + lower_result.translate((shift, -shift, z_shift))
            + lower_result.translate((shift, shift, z_shift))
            + lower_result.translate((-shift, -shift, z_shift))
        )

        combined = (group_a + group_b).translate((0, 0, height - layer_height_2))
        return (combined - self.make_gaps(order)) + self.make_ribs(order)

    def make_stand(self, order):
        """Build the printable stand beneath the full octahedroflake."""

        result = self.make_fractal_pyramid(order)
        factor = 2**order
        shift = self.dimensions.edge_size / 2 * factor
        solid_base = self.make_base_plate(self.dimensions.edge_size * (2**(order + 1)))

        combined_stand = (
            result.translate((-shift, shift, 0))
            + result.translate((shift, -shift, 0))
            + result.translate((shift, shift, 0))
            + result.translate((-shift, -shift, 0))
        )
        full_structure = combined_stand + self.make_ribs(order + 1) + solid_base
        return full_structure - self.make_gaps(order + 1)

    def export_pyramid(self, pyramid):
        """Export the upper pyramid half with its solid print base."""

        base_size = self.dimensions.edge_size * (2**self.config.iterations)
        solid_base = self.make_base_plate(base_size)
        pyramid_with_base = pyramid + solid_base
        self.export_result(pyramid_with_base, name=self.pyramid_name(), path=self.output_directory())

    def make_octahedron_fractal_with_stand(self):
        """Build the full printable model."""

        self.report('💠 make it!', order=self.config.iterations)
        pyramid = self.make_fractal_pyramid(self.config.iterations)
        self.export_pyramid(pyramid)
        mirrored = pyramid.mirror((0, 0, 1)).translate((0, 0, self.config.layer_height))
        combined_model = (pyramid + mirrored).translate((0, 0, self.dimensions.pyramid_height * (2**self.config.iterations)))
        self.report('🔗 combine with stand', order=self.config.iterations)
        return combined_model + self.make_stand(max(0, self.config.iterations - 2))

    def run(self):
        """Generate the model, export STL assets, and print runtime stats."""

        start_time = timeit.default_timer()
        self.report('*START*', order=self.config.iterations, extra_line=True)
        self.report(f'full_size: {self.dimensions.full_size}')
        self.report(f'full height: {self.dimensions.full_height}')
        self.report(f'edge size: {self.dimensions.edge_size}')
        flake = self.make_octahedron_fractal_with_stand()
        self.export_result(flake, name=self.model_name(), path=self.output_directory())
        self.report('DONE!')
        self.report(f'Elapsed time: {self.format_elapsed_time(round(timeit.default_timer() - start_time, 2))}')
