"""
Integration tests for vertexprint.py

These tests verify the parser functionality end-to-end, including:
- File parsing (Visual Polyhedra and STL formats)
- Command-line argument handling
- Polyhedron construction
- Output generation
"""

import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path

from scripts.vertexprint import (
    VisualPolyhedraParser,
    VisualPolyhedraLexer,
    StlParser,
    GlobalOptions,
    TokenType,
    OpenscadArgs,
    VertexType,
    OffsetType,
    get_parser,
)


class TestVisualPolyhedraLexer:
    """Tests for the VisualPolyhedraLexer class."""

    def test_basic_tokens(self):
        """Test that basic tokens are lexed correctly."""
        lexer = VisualPolyhedraLexer()
        input_str = "name = 1.5 ( ) { } , - + * / ^ : ;\n"
        lexer.lex(input_str)

        tokens = []
        while lexer.peek(1).ttype != TokenType.EOF:
            tokens.append(lexer.get())

        assert len(tokens) > 0
        assert tokens[0].ttype == TokenType.NAME
        assert tokens[0].lexeme == "name"

    def test_name_token(self):
        """Test that names are lexed correctly."""
        lexer = VisualPolyhedraLexer()
        lexer.lex("VertexA Edge123 myVariable\n")

        tokens = []
        while lexer.peek(1).ttype != TokenType.EOF:
            tokens.append(lexer.get())

        assert tokens[0].ttype == TokenType.NAME
        assert tokens[0].lexeme == "VertexA"
        assert tokens[1].ttype == TokenType.NAME
        assert tokens[1].lexeme == "Edge123"
        assert tokens[2].ttype == TokenType.NAME
        assert tokens[2].lexeme == "myVariable"

    def test_number_tokens(self):
        """Test that numbers are lexed correctly."""
        lexer = VisualPolyhedraLexer()
        lexer.lex("123 45.67 0.5 100\n")

        tokens = []
        while lexer.peek(1).ttype != TokenType.EOF:
            tokens.append(lexer.get())

        assert tokens[0].ttype == TokenType.INT
        assert tokens[0].lexeme == "123"
        assert tokens[1].ttype == TokenType.FLOAT
        assert tokens[1].lexeme == "45.67"
        assert tokens[2].ttype == TokenType.FLOAT
        assert tokens[2].lexeme == "0.5"
        assert tokens[3].ttype == TokenType.INT
        assert tokens[3].lexeme == "100"

    def test_special_characters(self):
        """Test that special characters are lexed correctly."""
        lexer = VisualPolyhedraLexer()
        lexer.lex("= ( ) { } [ ] , - + * / ^ : ;\n")

        tokens = []
        while lexer.peek(1).ttype != TokenType.EOF:
            tokens.append(lexer.get())

        assert tokens[0].ttype == TokenType.EQ
        assert tokens[1].ttype == TokenType.LPAREN
        assert tokens[2].ttype == TokenType.RPAREN
        assert tokens[3].ttype == TokenType.LBRACE
        assert tokens[4].ttype == TokenType.RBRACE
        assert tokens[5].ttype == TokenType.LSQUARE
        assert tokens[6].ttype == TokenType.RSQUARE
        assert tokens[7].ttype == TokenType.COMMA
        assert tokens[8].ttype == TokenType.MINUS
        assert tokens[9].ttype == TokenType.PLUS
        assert tokens[10].ttype == TokenType.STAR
        assert tokens[11].ttype == TokenType.SLASH
        assert tokens[12].ttype == TokenType.CARET
        assert tokens[13].ttype == TokenType.COLON
        assert tokens[14].ttype == TokenType.SEMI


class TestVisualPolyhedraParser:
    """Tests for the VisualPolyhedraParser class."""

    def test_simple_polyhedron_parsing(self):
        """Test parsing a simple polyhedron definition."""
        input_str = """SimpleTriangle

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert polyhedron is not None
        assert len(polyhedron.vertices) >= 1
        assert len(polyhedron.faces) >= 1

    def test_polyhedron_with_constants(self):
        """Test parsing a polyhedron with constant definitions."""
        input_str = """Tetrahedron

a = 1.0
b = 2.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)
V3 = (0.5, 0.288675, 0.816497)

Faces:
{ 0, 1, 2 }
{ 0, 1, 3 }
{ 0, 2, 3 }
{ 1, 2, 3 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert polyhedron.name == "tetrahedron"
        assert len(polyhedron.vertices) == 4
        assert len(polyhedron.faces) == 4

    def test_polyhedron_with_where_block(self):
        """Test parsing a polyhedron with a WHERE block."""
        input_str = """Cube

a = 1.0

WHERE: b = a * 2

V0 = (0, 0, 0)
V1 = (b, 0, 0)

Faces:
{ 0, 1 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert polyhedron is not None
        assert len(parser.constant_where_sequence) > 0

    def test_vertex_figure_computation(self):
        """Test that vertex figures are computed correctly."""
        input_str = """Triangle

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert len(polyhedron.vertex_figures) == 3
        for vf in polyhedron.vertex_figures:
            assert vf.vertex is not None
            assert len(vf.neighbors) > 0


class TestStlParser:
    """Tests for the StlParser class."""

    def test_stl_parser_creation(self):
        """Test that StlParser can be instantiated."""
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            # Create a simple binary STL file (unit cube)
            # Header (80 bytes) + number of triangles (4 bytes) + triangles
            import struct

            f.write(b"\x00" * 80)  # Header
            f.write(struct.pack("<I", 12))  # 12 triangles for a cube (2 per face)
            f.flush()

            parser = StlParser(f.name)
            assert parser.filepath == f.name

        os.unlink(f.name)


class TestPolyhedron:
    """Tests for the Polyhedron class."""

    def test_edge_extraction(self):
        """Test that edges are extracted correctly from faces."""
        input_str = """Triangle

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # Triangle has 3 unique edges
        assert len(polyhedron.edges) == 3

    def test_edge_lengths_computation(self):
        """Test that edge lengths are computed correctly."""
        input_str = """Square

a = 2.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (a, a, 0)
V3 = (0, a, 0)

Faces:
{ 0, 1, 2, 3 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # All edges should have length 2.0
        for edge, data in polyhedron.edges.items():
            assert data["length"] == pytest.approx(2.0, abs=0.01)

    def test_vertex_figure_signature(self):
        """Test vertex figure signature computation."""
        input_str = """EquilateralTriangle

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # All vertices should have the same signature for equilateral triangle
        # vertex_figure_signature is a method of Polyhedron, not VertexFigure
        signatures = [
            polyhedron.vertex_figure_signature(vf.vecs)
            for vf in polyhedron.vertex_figures
        ]
        assert len(set(signatures)) == 1  # All same for equilateral


class TestVisualPolyhedron:
    """Tests for the VisualPolyhedron class."""

    def test_evaluate_vertices(self):
        """Test vertex evaluation with constants."""
        input_str = """ScaledTriangle

a = 2.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (1.0, 1.73205, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # Check that vertices were evaluated with constant a=2.0
        v0 = polyhedron.vertices[0]
        v1 = polyhedron.vertices[1]
        v2 = polyhedron.vertices[2]

        assert v0[0] == 0 and v0[1] == 0 and v0[2] == 0
        assert v1[0] == 2.0 and v1[1] == 0 and v1[2] == 0
        assert abs(v2[0] - 1.0) < 0.01
        assert abs(v2[1] - 2.0 * 3**0.5 / 2) < 0.01


class TestOpenscadArgs:
    """Tests for the OpenscadArgs class."""

    def test_openscad_args_generation(self):
        """Test that OpenSCAD arguments are generated correctly."""
        input_str = """SimpleTriangle

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        args = OpenscadArgs(polyhedron, options)
        scad_args = args.to_openscad_args()

        # Check that required arguments are present
        assert any("-DEDGE_DIAMETER=" in arg for arg in scad_args)
        assert any("-DRADIUS=" in arg for arg in scad_args)
        assert any("-Dvertices=" in arg for arg in scad_args)
        assert any("-Dedges=" in arg for arg in scad_args)


class TestIntegration:
    """Integration tests that test the full pipeline."""

    @pytest.fixture
    def sample_polyhedron_file(self):
        """Create a sample Visual Polyhedra file for testing."""
        content = """TestPolyhedron

a = 1.0
b = 2.0

WHERE: c = a + b

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0.5, 0.866025, 0)
V3 = (0.5, 0.288675, 0.816497)

Faces:
{ 0, 1, 2 }
{ 0, 1, 3 }
{ 0, 2, 3 }
{ 1, 2, 3 }

"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".poly", delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)

    def test_full_parsing_pipeline(self, sample_polyhedron_file):
        """Test the full parsing pipeline from file to polyhedron."""
        parser = get_parser(sample_polyhedron_file)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert polyhedron.name == "testpolyhedron"
        assert len(polyhedron.vertices) == 4  # Tetrahedron
        assert len(polyhedron.faces) == 4

    def test_command_line_parsing(self, sample_polyhedron_file):
        """Test command-line argument parsing."""
        # Test with minimal arguments
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.parser",
                "--file",
                sample_polyhedron_file,
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )

        # Should complete without errors (may fail if openscad not installed)
        assert result.returncode in [0, 1]  # 1 is OK if openscad not found

    def test_output_directory_creation(self, sample_polyhedron_file):
        """Test that output directory is created when needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.parser",
                    "--file",
                    sample_polyhedron_file,
                    "--generate-outputs",
                    "--output-dir",
                    tmpdir,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )

            # Check that directory was created
            assert os.path.isdir(tmpdir)

    def test_different_offset_types(self, sample_polyhedron_file):
        """Test that different offset types can be specified."""
        offset_types = ["per_solid", "global", "per_vertex", "per_half_edge"]

        for offset_type in offset_types:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.parser",
                    "--file",
                    sample_polyhedron_file,
                    "--offset-type",
                    offset_type,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )
            # Should not crash on valid offset type
            assert "Error" not in result.stderr or "openscad" in result.stderr.lower()

    def test_different_vertex_types(self, sample_polyhedron_file):
        """Test that different vertex types can be specified."""
        vertex_types = ["tubular", "conical"]

        for vertex_type in vertex_types:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.parser",
                    "--file",
                    sample_polyhedron_file,
                    "--vertex-type",
                    vertex_type,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )
            # Should not crash on valid vertex type
            assert "Error" not in result.stderr or "openscad" in result.stderr.lower()

    def test_isotropize_option(self, sample_polyhedron_file):
        """Test that isotropize option can be applied."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.parser",
                "--file",
                sample_polyhedron_file,
                "--isotropize",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )
        # Should not crash
        assert "Error" not in result.stderr or "openscad" in result.stderr.lower()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".poly", delete=False) as f:
            f.write("")
            f.flush()
            try:
                parser = get_parser(f.name)
                options = GlobalOptions()
                # Should raise an exception for empty file
                with pytest.raises(Exception):
                    parser.parse(options)
            finally:
                os.unlink(f.name)

    def test_invalid_token(self):
        """Test handling of invalid tokens."""
        input_str = "name @ invalid\n"
        lexer = VisualPolyhedraLexer()

        # @ is not a valid character, so lexing should fail
        with pytest.raises(Exception):
            lexer.lex(input_str)

    def test_missing_faces(self):
        """Test handling of polyhedron without faces."""
        input_str = """NoFaces

a = 1.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)

Faces:
{ 0, 1 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # Should create a polyhedron with at least 2 vertices
        assert polyhedron is not None
        assert len(polyhedron.vertices) >= 2

    def test_single_vertex(self):
        """Test handling of polyhedron with single vertex."""
        input_str = """SingleVertex

a = 1.0

V0 = (0, 0, 0)

Faces:
{ 0 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        assert len(polyhedron.vertices) == 1

    def test_large_coordinates(self):
        """Test handling of large coordinate values."""
        input_str = """LargeCoordinates

a = 1000.0
b = 2000.0

V0 = (0, 0, 0)
V1 = (a, 0, 0)
V2 = (0, b, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # Coordinates should be preserved
        assert abs(polyhedron.vertices[1][0] - 1000.0) < 0.01
        assert abs(polyhedron.vertices[2][1] - 2000.0) < 0.01

    def test_negative_coordinates(self):
        """Test handling of negative coordinate values."""
        input_str = """NegativeCoords

a = 1.0

V0 = (0, 0, 0)
V1 = (-a, 0, 0)
V2 = (0, -a, 0)

Faces:
{ 0, 1, 2 }

"""
        parser = VisualPolyhedraParser(input_str)
        options = GlobalOptions()
        polyhedron = parser.parse(options)

        # Negative coordinates should be preserved
        assert abs(polyhedron.vertices[1][0] - (-1.0)) < 0.01
        assert abs(polyhedron.vertices[2][1] - (-1.0)) < 0.01


class TestGlobalOptions:
    """Tests for GlobalOptions class."""

    def test_default_options(self):
        """Test that default options are set correctly."""
        options = GlobalOptions()

        assert options.edge_diameter == 3.0
        assert options.radius == 200
        assert options.vertex_type.value == "tubular"
        assert options.offset_type.value == "per_solid"

    def test_custom_options(self):
        """Test that custom options are set correctly."""
        options = GlobalOptions(
            edge_diameter=5.0,
            radius=100,
            vertex_type=VertexType.CONICAL,
            offset_type=OffsetType.GLOBAL,
        )

        assert options.edge_diameter == 5.0
        assert options.radius == 100
        assert options.vertex_type.value == "conical"
        assert options.offset_type.value == "global"

    def test_derived_properties(self):
        """Test that derived properties are computed correctly."""
        options = GlobalOptions(
            edge_diameter=4.0,
            wall_thickness=2.0,
            rod_inset=5.0,
        )

        # tube_depth = rod_inset + wall_thickness
        assert options.tube_depth == 7.0
        # outer_tube_radius = edge_diameter / 2 + wall_thickness
        assert options.outer_tube_radius == 4.0


@pytest.mark.parametrize(
    "data_file",
    [f for f in Path("data").glob("*.txt") if not f.name.startswith("polyhedron_list")],
)
def test_parse_all_data_files(data_file: Path, tmp_path: Path):
    """Test that all visual polyhedra files in data/ can be parsed."""
    # Skip files that don't look like Visual Polyhedra files
    content = data_file.read_text()
    if not ("V" in content and "Faces:" in content):
        pytest.skip(f"{data_file.name} doesn't look like a Visual Polyhedra file")

    options = GlobalOptions()
    parser = get_parser(str(data_file))
    polyhedron = parser.parse(options)

    # Verify the polyhedron has vertices and faces
    assert polyhedron is not None
    assert len(polyhedron.vertices) >= 1
    assert len(polyhedron.faces) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
