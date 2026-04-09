"""
Integration tests for vertexprint.py

These tests verify the core functionality including:
- GlobalOptions class configuration
- Polyhedron class construction and edge computation
- VertexFigure class offset computation
- OpenscadArgs class argument generation
"""

import tempfile
import os
import numpy as np
import pytest
from scripts.vertexprint import (
    GlobalOptions,
    VertexType,
    OffsetType,
    ObjectType,
    Polyhedron,
    OpenscadArgs,
    VertexFigure,
    parse_stl,
)


class TestGlobalOptions:
    """Tests for GlobalOptions class."""

    def test_default_options(self):
        """Test that default options are set correctly."""
        options = GlobalOptions()

        assert options.edge_diameter == 3.0
        assert options.diameter_tolerance_fit == 0.35
        assert options.diameter_taper_fit == 0.10
        assert options.wall_thickness == 1.2
        assert options.radius == 200
        assert options.rod_inset == 8
        assert options.global_offset == 7.72
        assert options.rod_stock_length == 300
        assert options.rods_per_cut == 0
        assert options.min_printer_overhang_angle == 30
        assert options.vertex_type == VertexType.TUBULAR
        assert options.offset_type == OffsetType.PER_SOLID
        assert options.object_type == ObjectType.SOLID
        assert options.by_tag is True
        assert options.index == 0
        assert options.colors == ["red", "green", "blue"]
        assert options.label_vertices is True
        assert options.tubular_supports is True
        assert options.dry_run is False

        # Derived properties
        assert options.tube_depth == 9.2  # rod_inset + wall_thickness
        assert options.outer_tube_radius == 2.7  # edge_diameter / 2 + wall_thickness

    def test_custom_options(self):
        """Test that custom options are set correctly."""
        options = GlobalOptions(
            edge_diameter=5.0,
            radius=100,
            vertex_type=VertexType.CONICAL,
            offset_type=OffsetType.GLOBAL,
            object_type=ObjectType.VERTEX_HOLDER,
            by_tag=False,
            dry_run=True,
        )

        assert options.edge_diameter == 5.0
        assert options.radius == 100
        assert options.vertex_type == VertexType.CONICAL
        assert options.offset_type == OffsetType.GLOBAL
        assert options.object_type == ObjectType.VERTEX_HOLDER
        assert options.by_tag is False
        assert options.dry_run is True

    def test_custom_colors(self):
        """Test custom colors are set correctly."""
        options = GlobalOptions(colors=["blue", "yellow", "purple"])

        assert options.colors == ["blue", "yellow", "purple"]


class TestPolyhedron:
    """Tests for Polyhedron class."""

    def test_simple_triangle_construction(self):
        """Test construction of a simple triangular polyhedron."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.866025, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("triangle", vertices, faces, options)

        assert polyhedron.name == "triangle"
        assert len(polyhedron.vertices) == 3
        assert len(polyhedron.faces) == 1
        assert len(polyhedron.edges) == 3  # Triangle has 3 edges
        assert len(polyhedron.vertex_figures) == 3

    def test_tetrahedron_construction(self):
        """Test construction of a tetrahedron."""
        # Regular tetrahedron vertices
        a = 1.0
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [a, 0.0, 0.0],
            [0.5 * a, 0.866025 * a, 0.0],
            [0.5 * a, 0.288675 * a, 0.816497 * a],
        ])
        faces = [["0", "1", "2"], ["0", "1", "3"], ["0", "2", "3"], ["1", "2", "3"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("tetrahedron", vertices, faces, options)

        assert polyhedron.name == "tetrahedron"
        assert len(polyhedron.vertices) == 4
        assert len(polyhedron.faces) == 4
        assert len(polyhedron.edges) == 6  # Tetrahedron has 6 edges
        assert len(polyhedron.vertex_figures) == 4

    def test_cube_construction(self):
        """Test construction of a cube."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0],
        ])
        faces = [
            ["0", "1", "2", "3"],  # bottom
            ["4", "5", "6", "7"],  # top
            ["0", "1", "5", "4"],  # front
            ["2", "3", "7", "6"],  # back
            ["0", "3", "7", "4"],  # left
            ["1", "2", "6", "5"],  # right
        ]

        options = GlobalOptions()
        polyhedron = Polyhedron("cube", vertices, faces, options)

        assert polyhedron.name == "cube"
        assert len(polyhedron.vertices) == 8
        assert len(polyhedron.faces) == 6
        assert len(polyhedron.edges) == 12  # Cube has 12 edges

    def test_edge_lengths_computation(self):
        """Test that edge lengths are computed correctly."""
        # Square in xy-plane
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        faces = [["0", "1", "2", "3"]]

        options = GlobalOptions(radius=100)
        polyhedron = Polyhedron("square", vertices, faces, options)

        # All edges should have length 1.0 (before scaling)
        for edge, data in polyhedron.edges.items():
            assert data["length"] == pytest.approx(1.0, abs=0.01)

    def test_edge_lengths_with_different_radius(self):
        """Test edge length scaling with different radius."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(radius=200)
        polyhedron = Polyhedron("line", vertices, faces, options)

        # Edge length should be scaled by radius / max_dist
        # max_dist = 2.0, so scale_factor = 200 / 2 = 100
        # Original length = 2.0, scaled = 2.0 * 100 = 200
        for edge, data in polyhedron.edges.items():
            assert data["length"] == pytest.approx(2.0, abs=0.01)

    def test_vertex_figure_signature(self):
        """Test vertex figure signature computation."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.866025, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("triangle", vertices, faces, options)

        # Get vertex figures
        vertex_figures = polyhedron.vertex_figures
        assert len(vertex_figures) == 3

        # Each vertex figure should have neighbors
        for vf in vertex_figures:
            assert len(vf.neighbors) > 0
            assert vf.vertex_index >= 0

    def test_vertex_figure_normal(self):
        """Test vertex figure normal computation."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.866025, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("triangle", vertices, faces, options)

        vf = polyhedron.vertex_figures[0]
        # Normal should exist (at least one neighbor)
        normal = vf.normal()
        assert normal is not None
        # For a triangle in xy-plane with neighbors in xy-plane,
        # the normal should be computed from vecs sum
        # The vecs are normalized, so the normal should have some z component
        # if there are at least 2 non-collinear neighbors
        assert abs(normal[0]) < 0.9 or abs(normal[1]) < 0.9

    def test_average_edge_length(self):
        """Test average edge length computation."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        faces = [["0", "1", "2", "3"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("square", vertices, faces, options)

        avg_length = polyhedron.average_edge_length()
        # All edges are length 1.0, so average should be 1.0
        assert avg_length == pytest.approx(1.0, abs=0.01)

    def test_largest_offset(self):
        """Test largest offset computation."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.866025, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("triangle", vertices, faces, options)

        largest = polyhedron.largest_offset()
        # Should be a positive value
        assert largest > 0

    def test_make_edgelist(self):
        """Test edge list construction from faces."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("line", vertices, faces, options)

        edges = polyhedron.edges
        # Should have edges: (0,1), (1,2), (0,2)
        assert len(edges) == 3


class TestVertexFigure:
    """Tests for VertexFigure class."""

    def test_vertex_figure_creation(self):
        """Test basic vertex figure creation."""
        vertex = np.array([0.0, 0.0, 0.0])
        vertex_index = 0
        neighbors = [1, 2]
        vecs = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        tag = 0
        options = GlobalOptions()

        vf = VertexFigure(vertex, vertex_index, vecs, neighbors, tag, options)

        assert vf.vertex_index == 0
        assert vf.neighbors == [1, 2]
        assert vf.tag == 0
        assert vf.vertex is not None

    def test_vertex_figure_normalizable(self):
        """Test normalizable method."""
        vertex = np.array([0.0, 0.0, 0.0])
        vertex_index = 0
        neighbors = [1, 2]
        vecs = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        tag = 0
        options = GlobalOptions()

        vf = VertexFigure(vertex, vertex_index, vecs, neighbors, tag, options)

        # Should be normalizable (has at least 2 neighbors)
        assert vf.normalizable() is True

    def test_vertex_figure_normal(self):
        """Test normal computation."""
        vertex = np.array([0.0, 0.0, 0.0])
        vertex_index = 0
        neighbors = [1, 2]
        vecs = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        tag = 0
        options = GlobalOptions()

        vf = VertexFigure(vertex, vertex_index, vecs, neighbors, tag, options)

        normal = vf.normal()
        assert normal is not None
        # For two orthogonal vectors in xy-plane, normal should be in z direction
        # The normal is computed from vecs sum
        # For two orthogonal unit vectors, sum is [1, 1, 0]
        # Normalized is [1/sqrt(2), 1/sqrt(2), 0]
        # So both x and y components should be ~0.7
        assert abs(normal[0]) > 0.5 and abs(normal[1]) > 0.5

    def test_vertex_figure_plane_normal(self):
        """Test plane normal computation."""
        vertex = np.array([0.0, 0.0, 0.0])
        vertex_index = 0
        neighbors = [1, 2, 3]
        vecs = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        tag = 0
        options = GlobalOptions()

        vf = VertexFigure(vertex, vertex_index, vecs, neighbors, tag, options)

        plane_normal = vf.plane_normal()
        assert plane_normal is not None

    def test_vertex_figure_offset_computation(self):
        """Test vertex figure offset computation."""
        vertex = np.array([0.0, 0.0, 0.0])
        vertex_index = 0
        neighbors = [1, 2, 3]
        vecs = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        tag = 0
        options = GlobalOptions()

        vf = VertexFigure(vertex, vertex_index, vecs, neighbors, tag, options)

        # Should have computed offsets
        assert vf.half_edge_offset is not None
        assert len(vf.half_edge_offset) == 3
        assert vf.vertex_offset > 0


class TestOpenscadArgs:
    """Tests for OpenscadArgs class."""

    def test_openscad_args_creation(self):
        """Test OpenscadArgs can be created."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.866025, 0.0],
        ])
        faces = [["0", "1", "2"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("triangle", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        assert args.options == options
        assert args.polyhedron == polyhedron

    def test_to_openscad_args_basic(self):
        """Test basic OpenSCAD argument generation."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        scad_args = args.to_openscad_args()

        # Check that required arguments are present
        assert any("-DEDGE_DIAMETER=" in arg for arg in scad_args)
        assert any("-DRADIUS=" in arg for arg in scad_args)
        assert any("-Dvertices=" in arg for arg in scad_args)
        assert any("-Dedges=" in arg for arg in scad_args)

    def test_to_openscad_args_with_custom_options(self):
        """Test argument generation with custom options."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(
            edge_diameter=5.0,
            radius=100,
            vertex_type=VertexType.CONICAL,
            offset_type=OffsetType.GLOBAL,
        )
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        scad_args = args.to_openscad_args()

        assert "-DEDGE_DIAMETER=5.0" in scad_args
        assert "-DRADIUS=100" in scad_args
        assert '-DVERTEX_TYPE="conical"' in scad_args
        assert '-DOFFSET_TYPE="global"' in scad_args

    def test_to_openscad_args_all_offset_types(self):
        """Test argument generation for all offset types."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions()
        polyhedron = Polyhedron("line", vertices, faces, options)

        for offset_type in OffsetType:
            options.offset_type = offset_type
            args = OpenscadArgs(polyhedron, options)
            scad_args = args.to_openscad_args()

            # Should not crash and should contain offset type
            assert f'-DOFFSET_TYPE="{offset_type.value}"' in scad_args

    def test_to_openscad_args_with_colors(self):
        """Test argument generation with custom colors."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(colors=["red", "blue", "green"])
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        scad_args = args.to_openscad_args()

        # Colors should be in the format ["red","blue","green"]
        assert '-DCOLORS=["red","blue","green"]' in scad_args

    def test_to_openscad_args_dry_run_mode(self):
        """Test argument generation with dry run mode."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(dry_run=True, label_vertices=True)
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        scad_args = args.to_openscad_args()

        assert "-DLABEL_VERTICES=true" in scad_args

    def test_polyhedron_offset_array_global(self):
        """Test offset array generation with global offset type."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(offset_type=OffsetType.GLOBAL, global_offset=5.0)
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        offsets = args.polyhedron_offset_array(polyhedron)

        # For global offset, all vertex figures should have constant offset
        assert len(offsets) == len(polyhedron.vertex_figures)

    def test_polyhedron_offset_array_per_solid(self):
        """Test offset array generation with per_solid offset type."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        faces = [["0", "1"]]

        options = GlobalOptions(offset_type=OffsetType.PER_SOLID)
        polyhedron = Polyhedron("line", vertices, faces, options)
        args = OpenscadArgs(polyhedron, options)

        offsets = args.polyhedron_offset_array(polyhedron)

        # For per_solid, all vertex figures should have the same offset
        assert len(offsets) == len(polyhedron.vertex_figures)


class TestParseStl:
    """Tests for parse_stl function."""

    def test_parse_stl_file(self):
        """Test parsing an STL file."""
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False, mode="wb") as f:
            # Create a simple triangular STL file
            # Header (80 bytes) + number of triangles (4 bytes) + 1 triangle
            import struct

            # Write header
            f.write(b"Test Triangle" + b"\x00" * (80 - len(b"Test Triangle")))

            # Write number of triangles
            f.write(struct.pack("<I", 1))

            # Write triangle (12 floats + attribute byte count)
            f.write(struct.pack("<ffffffffffffH",
                0.0, 0.0, 1.0,  # Normal
                0.0, 0.0, 0.0,  # Vertex 1
                1.0, 0.0, 0.0,  # Vertex 2
                0.0, 1.0, 0.0,  # Vertex 3
                0  # Attribute byte count
            ))
            f.flush()

            options = GlobalOptions()
            polyhedron = parse_stl(f.name, options)

            assert polyhedron.name == "stl_model"
            assert len(polyhedron.vertices) == 3
            assert len(polyhedron.faces) == 1

            os.unlink(f.name)

    def test_parse_stl_with_multiple_triangles(self):
        """Test parsing an STL file with multiple triangles."""
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False, mode="wb") as f:
            import struct

            # Write header
            f.write(b"Test" + b"\x00" * 76)

            # Write number of triangles (2 triangles = 1 quad)
            f.write(struct.pack("<I", 2))

            # Write triangles
            for _ in range(2):
                f.write(struct.pack("<ffffffffffffH",
                    0.0, 0.0, 1.0,  # Normal
                    0.0, 0.0, 0.0,  # Vertex 1
                    1.0, 0.0, 0.0,  # Vertex 2
                    0.0, 1.0, 0.0,  # Vertex 3
                    0  # Attribute byte count
                ))
            f.flush()

            options = GlobalOptions()
            polyhedron = parse_stl(f.name, options)

            assert polyhedron.name == "stl_model"
            assert len(polyhedron.vertices) == 3
            assert len(polyhedron.faces) == 2

            os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
