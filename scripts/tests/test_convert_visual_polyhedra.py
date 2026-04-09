"""
Integration tests for convert_visual_polyhedra.py

These tests verify the Visual Polyhedra to OBJ conversion functionality:
- File parsing
- OBJ output generation
- Command-line interface
- Constant evaluation
"""

import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path

from scripts.convert_visual_polyhedra import (
    VisualPolyhedraParser,
    parse_visual_polyhedra_file,
)


class TestVisualPolyhedronToObj:
    """Tests for the VisualPolyhedron.to_obj() method."""

    def test_to_obj_basic_cube(self):
        """Test converting a simple cube to OBJ format."""
        input_str = """Cube

V0 = (0, 0, 0)
V1 = (1, 0, 0)
V2 = (1, 1, 0)
V3 = (0, 1, 0)

Faces:
{ 0, 1, 2, 3 }

"""
        parser = VisualPolyhedraParser(input_str)
        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Should have 4 vertices
            assert content.count("v ") == 4
            # Should have 1 face with 4 vertices
            assert "f 1 2 3 4" in content
        finally:
            os.unlink(output_path)

    def test_to_obj_preserves_polygonal_faces(self):
        """Test that faces with more than 3 vertices are preserved."""

        input_str = """SquareFace

V0 = (0, 0, 0)
V1 = (1, 0, 0)
V2 = (1, 1, 0)
V3 = (0, 1, 0)
V4 = (0.5, 0.5, 1)

Faces:
{ 0, 1, 2, 3 }
{ 0, 1, 4 }
{ 1, 2, 4 }
{ 2, 3, 4 }
{ 3, 0, 4 }

"""

        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Should have 5 vertices
            assert content.count("v ") == 5
            # The square face should be preserved (4 vertices)
            assert "f 1 2 3 4" in content
        finally:
            os.unlink(output_path)

    def test_to_obj_with_constants(self):
        """Test that constants are evaluated correctly in OBJ output."""

        input_str = """ScaledTriangle

a = 2.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0, a, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # The vertex coordinates should use the evaluated constant (a = 2.0)
            assert "v 2.0 0.0 0.0" in content
            assert "v 0.0 2.0 0.0" in content
        finally:
            os.unlink(output_path)

    def test_to_obj_negative_coordinates(self):
        """Test that negative coordinates are handled correctly."""

        input_str = """NegativeCoords

V0 = (-1, -1, -1)
V1 = (1, -1, -1)
V2 = (0, 1, -1)
V3 = (0, 0, 1)

Faces:
{ 0, 1, 2 }
{ 0, 1, 3 }
{ 1, 2, 3 }
{ 2, 0, 3 }

"""
        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Should contain negative coordinates
            assert "v -1.0 -1.0 -1.0" in content
        finally:
            os.unlink(output_path)


class TestParseVisualPolyhedraFile:
    """Tests for the parse_visual_polyhedra_file function."""

    def test_parse_txt_file(self):
        """Test parsing a .txt file."""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                """Test

V0 = (0, 0, 0)

Faces:
{ 0 }

"""
            )
            input_path = f.name

        try:
            polyhedron = parse_visual_polyhedra_file(input_path)

            assert polyhedron.name == "test"
            assert len(polyhedron.vertices) == 1
            assert len(polyhedron.faces) == 1
        finally:
            os.unlink(input_path)

    def test_parse_poly_file(self):
        """Test parsing a .poly file."""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".poly", delete=False) as f:
            f.write(
                """TestPoly

V0 = (1, 1, 1)

Faces:
{ 0 }

"""
            )
            input_path = f.name

        try:
            polyhedron = parse_visual_polyhedra_file(input_path)

            assert polyhedron.name == "testpoly"
            assert len(polyhedron.vertices) == 1
        finally:
            os.unlink(input_path)


class TestMainIntegration:
    """Tests for the main() function with command-line interface."""

    def test_main_basic_conversion(self):
        """Test basic file conversion via main()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_path = os.path.join(tmpdir, "test.txt")
            with open(input_path, "w") as f:
                f.write(
                    """TestCube

V0 = (0, 0, 0)
V1 = (1, 0, 0)
V2 = (1, 1, 0)
V3 = (0, 1, 0)

Faces:
{ 0, 1, 2, 3 }

"""
                )

            output_path = os.path.join(tmpdir, "test.obj")

            # Run the conversion
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.convert_visual_polyhedra",
                    input_path,
                    "-o",
                    output_path,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert os.path.exists(output_path)

            with open(output_path, "r") as f:
                content = f.read()
            assert "v " in content

    def test_main_automatic_output_path(self):
        """Test automatic output path generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "cube.txt")
            expected_output = os.path.join(tmpdir, "cube.obj")

            with open(input_path, "w") as f:
                f.write(
                    """Cube

V0 = (0, 0, 0)

Faces:
{ 0 }

"""
                )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.convert_visual_polyhedra",
                    input_path,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert os.path.exists(expected_output)

    def test_main_help_flag(self):
        """Test that --help flag works."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.convert_visual_polyhedra",
                "--help",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Convert Visual Polyhedra files to OBJ format" in result.stdout
        assert "-h" in result.stdout or "--help" in result.stdout

    def test_main_with_cube_data(self):
        """Test conversion of actual Cube.txt data file."""
        data_dir = Path(__file__).parent.parent.parent / "data"
        cube_path = data_dir / "Cube.txt"

        if cube_path.exists():
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "cube.obj")

                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "scripts.convert_visual_polyhedra",
                        str(cube_path),
                        "-o",
                        output_path,
                    ],
                    capture_output=True,
                    text=True,
                )

                assert result.returncode == 0
                assert os.path.exists(output_path)

                with open(output_path, "r") as f:
                    content = f.read()
                assert "v " in content
                assert "f " in content
                # Cube has 8 vertices and 6 faces
                assert content.count("v ") == 8
                assert content.count("f ") == 6


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self):
        """Test handling of empty file."""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            input_path = f.name

        try:
            with pytest.raises(Exception):
                parse_visual_polyhedra_file(input_path)
        finally:
            os.unlink(input_path)

    def test_single_vertex(self):
        """Test handling of polyhedron with single vertex."""

        input_str = """SingleVertex

V0 = (0, 0, 0)

Faces:
{ 0 }

"""
        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            assert content.count("v ") == 1
        finally:
            os.unlink(output_path)

    def test_large_coordinates(self):
        """Test handling of large coordinate values."""

        input_str = """LargeCoords

a = 1000.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0, a, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            assert "v 1000.0 0.0 0.0" in content
        finally:
            os.unlink(output_path)

    def test_multiple_faces(self):
        """Test conversion with multiple faces."""

        input_str = """MultiFace

V0 = (0, 0, 0)
V1 = (1, 0, 0)
V2 = (1, 1, 0)
V3 = (0, 1, 0)
V4 = (0, 0, 1)

Faces:
{ 0, 1, 2, 3 }
{ 0, 1, 4 }
{ 1, 2, 4 }
{ 2, 3, 4 }
{ 3, 0, 4 }

"""
        parser = VisualPolyhedraParser(input_str)

        class SimpleOptions:
            pass

        polyhedron = parser.parse()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
            output_path = f.name

        try:
            polyhedron.to_obj(output_path)

            with open(output_path, "r") as f:
                content = f.read()

            assert content.count("v ") == 5
            assert content.count("f ") == 5
        finally:
            os.unlink(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
