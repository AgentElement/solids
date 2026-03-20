from enum import Enum
from typing import Optional

import argparse
import os
import glob
import subprocess
import copy

import numpy as np
import pymeshlab
import stl_reader


class TokenType(Enum):
    NAME = 0
    EQ = 1
    LPAREN = 3
    RPAREN = 4
    LBRACE = 5
    RBRACE = 6
    COMMA = 7
    FLOAT = 8
    INT = 9
    MINUS = 10
    NEWLINE = 11
    STAR = 12
    PLUS = 13
    CARET = 14
    SLASH = 15
    COLON = 16
    EOF = 17
    LSQUARE = 18
    RSQUARE = 19
    SEMI = 20


class VertexType(Enum):
    TUBULAR = "tubular"
    CONICAL = "conical"


class OffsetType(Enum):
    PER_SOLID = "per_solid"
    GLOBAL = "global"
    PER_VERTEX = "per_vertex"
    PER_HALF_EDGE = "per_half_edge"


class ObjectType(Enum):
    VERTEX_HOLDER = "vertex_holder"
    SOLID = "solid"
    ALL_VERTEX_HOLDERS = "all_vertex_holders"


# A subset of openscad's tokens, plus tokens for David McCooey's visual
# polyhedra files
class Token:
    def __init__(
        self, ttype: TokenType, lexeme: Optional[str], pos: int, line: int, column: int
    ) -> None:
        self.ttype = ttype
        self.lexeme = lexeme
        self.pos = pos
        self.line = line
        self.column = column

    def literal(self) -> str:
        match self.ttype:
            case TokenType.NAME | TokenType.FLOAT | TokenType.INT:
                return str(self.lexeme)
            case TokenType.EQ:
                return "="
            case TokenType.LPAREN:
                return "("
            case TokenType.RPAREN:
                return ")"
            case TokenType.LBRACE:
                return "{"
            case TokenType.RBRACE:
                return "}"
            case TokenType.LSQUARE:
                return "["
            case TokenType.RSQUARE:
                return "]"
            case TokenType.COMMA:
                return ","
            case TokenType.MINUS:
                return "-"
            case TokenType.NEWLINE:
                return "\n"
            case TokenType.STAR:
                return "*"
            case TokenType.PLUS:
                return "+"
            case TokenType.CARET:
                return "^"
            case TokenType.SLASH:
                return "/"
            case TokenType.COLON:
                return ":"
            case TokenType.EOF:
                return "\0"
            case TokenType.SEMI:
                return ";"
            case _:
                raise Exception(f"Bad token type: {self.ttype}")

    def __str__(self) -> str:
        return f"{self.pos} {self.ttype} {self.lexeme}"


# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Geometry                                                                  │
# └───────────────────────────────────────────────────────────────────────────┘


class GlobalOptions:
    def __init__(
        self,
        edge_diameter: float = 3.0,
        diameter_tolerance_fit: float = 0.35,
        diameter_taper_fit: float = 0.10,
        wall_thickness: float = 1.2,
        radius: float = 200,
        rod_inset: float = 8,
        global_offset: float = 7.72,
        min_printer_overhang_angle: float = 30,
        vertex_type: VertexType = VertexType.TUBULAR,
        offset_type: OffsetType = OffsetType.PER_SOLID,
        object_type: ObjectType = ObjectType.SOLID,
        by_tag: bool = True,
        index: int = 0,
        colors: Optional[list[str]] = None,
        label_vertices: bool = True,
        tubular_supports: bool = True,
    ) -> None:
        self.edge_diameter = edge_diameter
        self.diameter_tolerance_fit = diameter_tolerance_fit
        self.diameter_taper_fit = diameter_taper_fit
        self.wall_thickness = wall_thickness
        self.radius = radius
        self.rod_inset = rod_inset
        self.global_offset = global_offset
        self.min_printer_overhang_angle = min_printer_overhang_angle
        self.vertex_type = vertex_type
        self.offset_type = offset_type
        self.object_type = object_type
        self.by_tag = by_tag
        self.index = index
        self.colors = colors if colors is not None else ["red", "green", "blue"]
        self.label_vertices = label_vertices
        self.tubular_supports = tubular_supports

        self.tube_depth = rod_inset + wall_thickness
        self.outer_tube_radius = edge_diameter / 2 + wall_thickness


class VertexFigure:
    def __init__(
        self,
        vertex: np.ndarray,
        vertex_index: int,
        vecs: np.ndarray,
        neighbors: list[int],
        tag: int,
        options: GlobalOptions,
    ) -> None:
        self.vertex = vertex
        self.vertex_index = vertex_index
        self.vecs = vecs
        self.neighbors = neighbors

        self.std = vecs
        self.euler = [0, 0, 0]
        self.options = options

        self.half_edge_offset = self.compute_offsets()
        self.vertex_offset = self.largest_offset()

        plane_normal = self.plane_normal()
        normal = self.normal()
        if normal is not None and plane_normal is not None:
            direction = 1 if np.dot(plane_normal, normal) > 0 else -1
            rotated, euler = self.reorient_to(direction * plane_normal)
            self.std = rotated
            self.euler = euler

        self.tag = tag

    def annotate_edge_names(self, edges: dict[tuple[int, int], dict[str, ...]]):
        self.edges = []
        for neighbor in self.neighbors:
            edge = (
                (self.vertex_index, neighbor)
                if self.vertex_index < neighbor
                else (neighbor, self.vertex_index)
            )
            self.edges.append(edges[edge]["name"])

    def normalizable(self) -> bool:
        return self.normal() is not None

    def normal(self) -> Optional[np.ndarray]:
        n = np.sum(self.vecs, axis=0)
        norm = np.linalg.norm(n)
        return n / norm if norm > 1e-10 else None

    def plane_normal(self) -> Optional[np.ndarray]:
        vecs = copy.deepcopy(self.vecs)
        if self.options.offset_type == OffsetType.PER_HALF_EDGE:
            vecs *= self.half_edge_offset[:, np.newaxis] + self.options.rod_inset
        if len(vecs) < 3:
            return None
        center = np.mean(vecs, axis=0)
        centered = vecs - center
        _, _, vh = np.linalg.svd(centered)
        normal = vh[2]
        return -normal / np.linalg.norm(normal)

    def matrix_to_rotation(self, R: np.ndarray) -> list[float]:
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6
        if not singular:
            return [
                float(np.atan2(R[2, 1], R[2, 2])),
                float(np.atan2(-R[2, 0], sy)),
                float(np.atan2(R[1, 0], R[0, 0])),
            ]
        # Handle gimbal lock cases
        elif R[2, 0] < 0:
            # y = 90 degrees
            return [float(np.atan2(-R[1, 2], R[1, 1])), 90, 0]
        else:
            # y = -90 degrees
            return [float(np.atan2(-R[1, 2], R[1, 1])), -90, 0]

    # Orient normal to target, then apply this rotation to all vectors in the
    # figure
    def reorient_to(
        self, normal, target=np.array([0, 0, 1])
    ) -> tuple[np.ndarray, list[float]]:
        nn = np.linalg.norm(normal)
        if nn < 1e-9:
            return (self.vecs, [0, 0, 0])
        u_mean = normal / nn
        axis = np.cross(u_mean, target)
        len_axis = np.linalg.norm(axis)
        dot_val = np.dot(u_mean, target)
        if len_axis < 1e-6:
            if dot_val > 0:
                return (self.vecs, [0, 0, 0])
            else:
                flipped = np.array([np.array([v[0], -v[1], -v[2]]) for v in self.vecs])
                return (flipped, [180, 0, 0])
        u = axis / len_axis
        c = dot_val
        s = len_axis
        C = 1 - c
        R = np.array(
            [
                [
                    c + u[0] * u[0] * C,
                    u[0] * u[1] * C - u[2] * s,
                    u[0] * u[2] * C + u[1] * s,
                ],
                [
                    u[1] * u[0] * C + u[2] * s,
                    c + u[1] * u[1] * C,
                    u[1] * u[2] * C - u[0] * s,
                ],
                [
                    u[2] * u[0] * C - u[1] * s,
                    u[2] * u[1] * C + u[0] * s,
                    c + u[2] * u[2] * C,
                ],
            ]
        )
        euler = self.matrix_to_rotation(R.T)
        rotated = np.array([R @ v for v in self.vecs])
        return (rotated, euler)

    def min_cos_dist(self, index: int) -> np.ndarray:
        scores = [
            -1000
            if i == index
            else (self.vecs[index] @ self.vecs[i]) / np.linalg.norm(self.vecs[i])
            for i in range(1, len(self.vecs))
        ]
        max_score = max(scores)
        max_idx = scores.index(max_score)
        return self.vecs[max_idx + 1]

    def axis_offset(self, v0: np.ndarray, v1: np.ndarray) -> float:
        c = np.dot(v0, v1)
        s = np.linalg.norm(np.cross(v0, v1))
        l_side = (
            self.options.outer_tube_radius * c + self.options.edge_diameter / 2
        ) / s
        l_base = (self.options.edge_diameter / 2 * (1 + c)) / s
        if s < 1e-9:
            return 1e9 if c > 0 else 0
        return max(l_side, l_base)

    def offset_from_single_vec(self, index: int) -> float:
        closest = self.min_cos_dist(index)
        return self.axis_offset(self.vecs[index], closest)

    def compute_offsets(self):
        return np.array([self.offset_from_single_vec(i) for i in range(len(self.vecs))])

    def largest_offset(self):
        return max(self.half_edge_offset)


class Polyhedron:
    def __init__(self, name, vertices, faces, options: GlobalOptions) -> None:
        self.name = name
        self.faces = faces
        self.vertices: np.ndarray = vertices
        self.options = options

        self.edges: dict[tuple[int, int], dict[str, ...]] = self.make_edgelist()
        self.vertex_figures = self.annotate_vertex_figures()
        self.solid_offset = self.largest_offset()
        self.compute_edge_lengths()
        for vf in self.vertex_figures:
            vf.annotate_edge_names(self.edges)

    def average_edge_length(self) -> float:
        return np.sum([e["length"] for e in self.edges.values()]) / len(self.edges)

    def largest_offset(self) -> float:
        if len(self.vertex_figures) == 0:
            return 0
        offsets = [vf.vertex_offset for vf in self.vertex_figures]
        return max(offsets)

    def print_offset_edge_lengths(self):
        sorted_edges = sorted(self.edges.items(), key=lambda x: x[1]["offset_length"])
        for edge, data in sorted_edges:
            print(f"({data['name']}, {data['offset_length']:.6f})")

    def offset_for_edge(self, v1, v2):
        vf1 = self.vertex_figures[v1]
        vf2 = self.vertex_figures[v2]
        match self.options.offset_type:
            case OffsetType.GLOBAL:
                return (self.options.global_offset, self.options.global_offset)
            case OffsetType.PER_VERTEX:
                return (
                    vf1.vertex_offset,
                    vf2.vertex_offset,
                )
            case OffsetType.PER_HALF_EDGE:
                v1_neighbor = next(ix for ix, n in enumerate(vf1.neighbors) if n == v2)
                v2_neighbor = next(ix for ix, n in enumerate(vf2.neighbors) if n == v1)
                return (
                    vf1.half_edge_offset[v1_neighbor],
                    vf2.half_edge_offset[v2_neighbor],
                )
            case OffsetType.PER_SOLID | _:
                return (self.solid_offset, self.solid_offset)

    def compute_edge_lengths(self):
        edge_lengths = []
        max_dist = max([np.linalg.norm(v) for v in self.vertices])
        for v1, v2 in self.edges:
            v1_offset, v2_offset = self.offset_for_edge(v1, v2)
            v1_arr = self.vertices[v1]
            v2_arr = self.vertices[v2]
            length = np.linalg.norm(v2_arr - v1_arr)
            scale_factor = self.options.radius / max_dist
            offset_length = scale_factor * length - v1_offset - v2_offset
            edge_lengths.append(((v1, v2), length, offset_length))

        sorted_edges = sorted(edge_lengths, key=lambda x: x[2])
        for i, (edge, length, offset_length) in enumerate(sorted_edges):
            self.edges[edge] = {
                "length": length,
                "offset_length": offset_length,
                "name": i,
            }

    # Convert facelist into edgelist
    def make_edgelist(self) -> dict[tuple[int, int], list[...]]:
        edges = set()
        for face in self.faces:
            for v1, v2 in zip(face, face[1:] + [face[0]]):
                v1_int = int(v1)
                v2_int = int(v2)
                if v1_int < len(self.vertices) and v2_int < len(self.vertices):
                    edges.add((v1_int, v2_int) if v1_int < v2_int else (v2_int, v1_int))
        return {e: [] for e in edges}

    def vertex_figure_signature(self, vecs) -> tuple[int, ...]:
        precision = 100000
        n = len(vecs)
        dots = sorted(
            [
                round(np.dot(vecs[i], vecs[j]) * precision)
                for i in range(n)
                for j in range(i, n)
            ]
        )
        triples = sorted(
            [
                round(np.dot(np.cross(vecs[i], vecs[j]), vecs[k]) * precision)
                for i in range(n)
                for j in range(n)
                for k in range(n)
            ]
        )
        return tuple(dots + triples)

    def annotate_vertex_figures(self) -> list[VertexFigure]:
        vertices_arr = self.vertices

        tags = {}
        tag = 0
        vertex_figures = []
        for i, vertex in enumerate(vertices_arr):
            neighbors = [
                e[1] if e[0] == i else (e[0] if e[1] == i else None)
                for e in self.edges.keys()
            ]
            neighbors = [n for n in neighbors if n is not None]
            vecs = [(vertices_arr[n] - vertex) for n in neighbors]
            vecs = [
                v / (np.linalg.norm(v) if np.linalg.norm(v) > 0 else 1) for v in vecs
            ]
            signature = self.vertex_figure_signature(vecs)
            if signature not in tags:
                tags[signature] = tag
                tag += 1

            vertex_figures.append(
                VertexFigure(
                    vertex,
                    i,
                    np.array(vecs),
                    neighbors,
                    tags[signature],
                    self.options,
                )
            )

        return vertex_figures

    def isotropize(self):
        ms = pymeshlab.MeshSet()

        ms.add_mesh(pymeshlab.Mesh(self.vertices, self.faces))

        average_edge_length = self.average_edge_length()

        ms.apply_filter(
            "meshing_isotropic_explicit_remeshing",
            iterations=8,
            targetlen=pymeshlab.PureValue(average_edge_length),
            featuredeg=15,
            adaptive=False,
        )

        mesh = ms.current_mesh()

        self.__init__(
            vertices=mesh.vertex_matrix(),
            faces=mesh.face_matrix().tolist(),
            name=self.name,
            options=self.options,
        )


class VisualPolyhedron(Polyhedron):
    def __init__(
        self,
        name,
        vertex_tokenstream,
        faces,
        constant_exacts,
        constant_floats,
        constant_sequence,
        options: GlobalOptions,
    ) -> None:
        self.vertex_tokenstream = vertex_tokenstream

        self.faces = faces
        self.name = name

        self.constant_exacts = constant_exacts
        self.constant_floats = constant_floats
        self.constant_sequence = constant_sequence

        vertices: np.ndarray = self.evaluate_vertices()

        super().__init__(name, vertices, faces, options)

    def evaluate_vertices(self):
        vertices = {}
        for vertex, token_list in self.vertex_tokenstream.items():
            evaluated = []
            neg = 1
            for token in token_list:
                match token.ttype:
                    case TokenType.LSQUARE | TokenType.RSQUARE:
                        continue
                    case TokenType.COMMA:
                        neg = 1
                    case TokenType.MINUS:
                        neg = -1
                    case TokenType.FLOAT:
                        evaluated.append(neg * float(token.lexeme))
                    case TokenType.NAME:
                        evaluated.append(neg * self.constant_floats[token.lexeme])
                    case _:
                        raise ValueError(
                            "Bad token encountered while evaluating vertices"
                        )

            vertices[int(vertex[1:])] = evaluated
        vertex_keys = sorted(vertices.keys())
        vertices = np.array([vertices[v] for v in vertex_keys])
        return vertices

    def openscad_vertices(self) -> list[Token]:
        tokenstream = [
            Token(TokenType.NAME, f"{self.name}_vertices", -1, -1, -1),
            Token(TokenType.EQ, None, -1, -1, -1),
            Token(TokenType.LSQUARE, None, -1, -1, -1),
            Token(TokenType.NEWLINE, None, -1, -1, -1),
        ]
        for vertex, token_list in self.vertex_tokenstream.items():
            for token in token_list:
                if token.ttype == TokenType.NAME:
                    token.lexeme = f"{self.name}_{token.lexeme}"
                tokenstream.append(token)
            tokenstream.append(Token(TokenType.COMMA, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.RSQUARE, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.SEMI, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.NEWLINE, None, -1, -1, -1))
        return tokenstream

    def openscad_constants(self) -> list[Token]:
        tokenstream = []
        seen_constants = set()
        for constant in self.constant_sequence:
            if constant in seen_constants:
                continue
            tokenstream.append(
                Token(TokenType.NAME, f"{self.name}_{constant}", -1, -1, -1)
            )
            tokenstream.append(Token(TokenType.EQ, None, -1, -1, -1))
            if constant in self.constant_exacts:
                for token in self.constant_exacts[constant]:
                    lexeme = token.lexeme
                    if (
                        token.ttype == TokenType.NAME
                        and lexeme in self.constant_sequence
                    ):
                        tokenstream.append(
                            Token(TokenType.NAME, f"{self.name}_{lexeme}", -1, -1, -1)
                        )
                    else:
                        tokenstream.append(token)
            else:
                tokenstream += self.constant_floats[constant]
            tokenstream.append(Token(TokenType.SEMI, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1, -1, -1))
        return tokenstream

    def openscad_edges(self) -> list[Token]:
        tokenstream = [
            Token(TokenType.NAME, f"{self.name}_edges", -1, -1, -1),
            Token(TokenType.EQ, None, -1, -1, -1),
            Token(TokenType.LSQUARE, None, -1, -1, -1),
            Token(TokenType.NEWLINE, None, -1, -1, -1),
        ]
        for start, end in sorted(self.edges.keys()):
            tokenstream.append(Token(TokenType.LSQUARE, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.NAME, str(start), -1, -1, -1))
            tokenstream.append(Token(TokenType.COMMA, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.NAME, str(end), -1, -1, -1))
            tokenstream.append(Token(TokenType.RSQUARE, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.COMMA, None, -1, -1, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.RSQUARE, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.SEMI, None, -1, -1, -1))
        tokenstream.append(Token(TokenType.NEWLINE, None, -1, -1, -1))
        return tokenstream

    def openscad(self) -> str:
        tokenstream = self.openscad_constants()
        tokenstream += self.openscad_vertices()
        tokenstream += self.openscad_edges()
        return "".join([x.literal() for x in tokenstream])


class OpenscadArgs:
    def __init__(self, polyhedron: Polyhedron, options: GlobalOptions):
        self.options = options
        self.polyhedron = polyhedron

        vertices, edges, vertex_figures, eulers, tags, vertex_figure_edges = (
            self.polyhedron_options_array(polyhedron)
        )
        self.vertices = vertices
        self.edges = edges
        self.vertex_figures = vertex_figures
        self.eulers = eulers
        self.tags = tags
        self.vertex_figure_edges = vertex_figure_edges
        self.offsets = self.polyhedron_offset_array(polyhedron)

    def polyhedron_options_array(self, polyhedron: Polyhedron):
        vertices = polyhedron.vertices
        edges = polyhedron.edges.keys()
        vertex_figures = []
        eulers = []
        tags = []
        vertex_figure_edges = []

        for vertex_figure in polyhedron.vertex_figures:
            vertex_figures.append(vertex_figure.std)
            eulers.append(vertex_figure.euler)
            tags.append(vertex_figure.tag)
            vertex_figure_edges.append(vertex_figure.edges)

        return vertices, edges, vertex_figures, eulers, tags, vertex_figure_edges

    def polyhedron_offset_array(self, polyhedron: Polyhedron) -> list[...]:
        match self.options.offset_type:
            case OffsetType.GLOBAL:
                value = self.options.global_offset
                return [[value] * len(vf.vecs) for vf in polyhedron.vertex_figures]
            case OffsetType.PER_VERTEX:
                return [
                    [vf.vertex_offset] * len(vf.vecs)
                    for vf in polyhedron.vertex_figures
                ]
            case OffsetType.PER_HALF_EDGE:
                return [vf.half_edge_offset for vf in polyhedron.vertex_figures]
            case OffsetType.PER_SOLID | _:
                value = polyhedron.solid_offset
                return [[value] * len(vf.vecs) for vf in polyhedron.vertex_figures]

    def to_openscad_args(self) -> list[str]:
        args = []
        args.append(f"-DEDGE_DIAMETER={self.options.edge_diameter}")
        args.append(f"-DDIAMETER_TOLERANCE_FIT={self.options.diameter_tolerance_fit}")
        args.append(f"-DDIAMETER_TAPER_FIT={self.options.diameter_taper_fit}")
        args.append(f"-DWALL_THICKNESS={self.options.wall_thickness}")
        args.append(f"-DRADIUS={self.options.radius}")
        args.append(f"-DROD_INSET={self.options.rod_inset}")
        args.append(f"-DGLOBAL_OFFSET={self.options.global_offset}")
        args.append(
            f"-DMIN_PRINTER_OVERHANG_ANGLE={self.options.min_printer_overhang_angle}"
        )
        args.append(f'-DVERTEX_TYPE="{self.options.vertex_type.value}"')
        args.append(f'-DOFFSET_TYPE="{self.options.offset_type.value}"')
        args.append(f'-DOBJECT="{self.options.object_type.value}"')
        args.append(f"-DBY_TAG={'true' if self.options.by_tag else 'false'}")
        args.append(f"-DINDEX={self.options.index}")
        colors_str = "[" + ",".join(f'"{c}"' for c in self.options.colors) + "]"
        args.append(f"-DCOLORS={colors_str}")
        args.append(
            f"-DLABEL_VERTICES={'true' if self.options.label_vertices else 'false'}"
        )
        args.append(
            f"-DTUBULAR_SUPPORTS={'true' if self.options.tubular_supports else 'false'}"
        )
        vertices_str = (
            "["
            + ",".join(
                f"[{','.join(str(v) for v in vertex)}]" for vertex in self.vertices
            )
            + "]"
        )
        args.append(f"-Dvertices={vertices_str}")
        edges_str = (
            "[" + ",".join(f"[{start},{end}]" for start, end in self.edges) + "]"
        )
        args.append(f"-Dedges={edges_str}")
        vertex_figures_str = (
            "["
            + ",".join(
                f"[{','.join(str(v) for v in vf.tolist())}]"
                for vf in self.vertex_figures
            )
            + "]"
        )
        args.append(f"-Dvertex_figures={vertex_figures_str}")
        eulers_str = (
            "[" + ",".join(f"[{e[0]},{e[1]},{e[2]}]" for e in self.eulers) + "]"
        )
        args.append(f"-Deulers={eulers_str}")
        tags_str = "[" + ",".join(str(t) for t in self.tags) + "]"
        args.append(f"-Dtags={tags_str}")
        offsets_str = (
            "["
            + ",".join(
                "[" + ",".join(str(v) for v in o.tolist()) + "]"
                if hasattr(o, "tolist")
                else "[" + ",".join(str(v) for v in o) + "]"
                for o in self.offsets
            )
            + "]"
        )
        args.append(f"-Doffsets={offsets_str}")
        vertex_figure_edges_str = (
            "["
            + ",".join(
                f"[{','.join(str(e) for e in vf)}]" for vf in self.vertex_figure_edges
            )
            + "]"
        )
        args.append(f"-Dvertex_figure_edges={vertex_figure_edges_str}")
        return args


# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Polyhedron parsers                                                        │
# └───────────────────────────────────────────────────────────────────────────┘


# Parse STL files into Polyhedron objects using stl-reader library
class StlParser:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def parse(self, options: GlobalOptions) -> Polyhedron:
        vertices_arr, indices = stl_reader.read(self.filepath)

        return Polyhedron(
            name="stl_model",
            vertices=vertices_arr,
            faces=indices.tolist(),
            options=options,
        )


# Lex Visual Polyhedra files
class VisualPolyhedraLexer:
    def __init__(self) -> None:
        self.tokenstream = []
        self.pos = 0

    @staticmethod
    def munch_num(input: str, pos: int, line: int, column: int) -> tuple[Token, int]:
        lexeme = ""
        offset = 0
        while input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        if input[pos + offset] != ".":
            return (Token(TokenType.INT, lexeme, pos, line, column), offset)
        offset += 1
        lexeme += "."

        while input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.FLOAT, lexeme, pos, line, column), offset)

    @staticmethod
    def munch_name(input: str, pos: int, line: int, column: int) -> tuple[Token, int]:
        if not input[pos].isalpha():
            raise Exception(f"Cannot parse name at position {pos}")

        lexeme = input[pos]
        offset = 1

        while input[pos + offset].isalnum():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.NAME, lexeme, pos, line, column), offset)

    def lex(self, input: str):
        i = 0
        line = 1
        column = 1
        while i < len(input):
            match input[i]:
                case "(":
                    self.tokenstream.append(
                        Token(TokenType.LPAREN, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ")":
                    self.tokenstream.append(
                        Token(TokenType.RPAREN, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "{":
                    self.tokenstream.append(
                        Token(TokenType.LBRACE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "}":
                    self.tokenstream.append(
                        Token(TokenType.RBRACE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "=":
                    self.tokenstream.append(Token(TokenType.EQ, None, i, line, column))
                    i += 1
                    column += 1
                case "-":
                    self.tokenstream.append(
                        Token(TokenType.MINUS, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ",":
                    self.tokenstream.append(
                        Token(TokenType.COMMA, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "*":
                    self.tokenstream.append(
                        Token(TokenType.STAR, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "+":
                    self.tokenstream.append(
                        Token(TokenType.PLUS, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "/":
                    self.tokenstream.append(
                        Token(TokenType.SLASH, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "^":
                    self.tokenstream.append(
                        Token(TokenType.CARET, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ":":
                    self.tokenstream.append(
                        Token(TokenType.COLON, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "\n":
                    self.tokenstream.append(
                        Token(TokenType.NEWLINE, None, i, line, column)
                    )
                    i += 1
                    line += 1
                    column = 1
                case " " | "\t":
                    i += 1
                    column += 1
                case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                    (tok, offset) = self.munch_num(input, i, line, column)
                    self.tokenstream.append(tok)
                    i += offset
                    column += offset
                case _:
                    (tok, offset) = self.munch_name(input, i, line, column)
                    self.tokenstream.append(tok)
                    i += offset
                    column += offset
        self.tokenstream.append(Token(TokenType.EOF, None, i, line, column))

    def get(self) -> Token:
        token = self.tokenstream[self.pos]
        self.pos += 1
        return token

    def peek(self, i: int) -> Token:
        assert i >= 0
        assert self.pos + i <= len(self.tokenstream)
        token = self.tokenstream[self.pos + i - 1]
        return token


# Constant definitions in visual polyhedra files can be followed by a 'where'
# block. This flag tells the parser that we are currently reading 'where'
# constants.
class ConstantRegion(Enum):
    DEF = 0
    WHERE = 1


# Parse visual polyhedra files to Polyhedron objects
class VisualPolyhedraParser:
    def __init__(self, input) -> None:
        self.lexer = VisualPolyhedraLexer()
        self.lexer.lex(input)

        self.vertices = {}
        self.faces = []
        self.name = None

        self.constant_exacts = {}
        self.constant_floats = {}
        self.constant_def_sequence = []
        self.constant_where_sequence = []
        self.constant_sequence = []

    def syntax_error(self):
        token = self.lexer.peek(0)
        raise Exception(f"Snytax Eorrr at position {token.pos}")

    @staticmethod
    def is_expression_ttype(ttype: TokenType) -> bool:
        match ttype:
            case (
                TokenType.INT
                | TokenType.NAME
                | TokenType.STAR
                | TokenType.PLUS
                | TokenType.MINUS
                | TokenType.LPAREN
                | TokenType.RPAREN
                | TokenType.SLASH
                | TokenType.CARET
            ):
                return True
            case _:
                return False

    def expect(self, ttype: TokenType) -> Token:
        token = self.lexer.get()
        if token.ttype != ttype:
            raise Exception(
                f"Expected {ttype} at line {token.line} and column {token.column}, found {token.ttype}"
            )

        return token

    def expect_expression(self) -> Token:
        token = self.lexer.get()
        if not self.is_expression_ttype(token.ttype):
            raise Exception(
                f"Expected expression token at position {token.pos}, found {token.ttype}"
            )

        return token

    def linebreak(self):
        self.expect(TokenType.NEWLINE)
        while self.lexer.peek(1).ttype == TokenType.NEWLINE:
            self.expect(TokenType.NEWLINE)

    # name_def := names* \n
    def name_def(self):
        names = []
        while self.lexer.peek(1).ttype in {
            TokenType.NAME,
            TokenType.LPAREN,
            TokenType.RPAREN,
        }:
            match self.lexer.peek(1).ttype:
                case TokenType.NAME:
                    names.append(self.expect(TokenType.NAME).lexeme)
                case TokenType.LPAREN:
                    self.expect(TokenType.LPAREN)
                case TokenType.RPAREN:
                    self.expect(TokenType.RPAREN)
        self.linebreak()
        self.name = "_".join(names).lower()

    # constant_def := name = float \n
    # constant_def := name = float = [int|name|*|(|)|+|/|*|^] \n
    # constant_def := name = [int|name|*|(|)|+|/|^] \n
    def constant_def(self, region: ConstantRegion):
        const = self.expect(TokenType.NAME).lexeme
        floatv = 0.0
        exactv = []

        self.expect(TokenType.EQ)
        ttype = self.lexer.peek(1).ttype
        if ttype == TokenType.FLOAT:
            floatv = self.expect(TokenType.FLOAT).literal()
            ttype = self.lexer.peek(1).ttype

            if ttype == TokenType.NEWLINE:
                pass
            elif ttype == TokenType.EQ:
                self.expect(TokenType.EQ)
                while self.is_expression_ttype(self.lexer.peek(1).ttype):
                    exactv.append(self.expect_expression())
            else:
                self.syntax_error()

        elif self.is_expression_ttype(ttype):
            while self.is_expression_ttype(self.lexer.peek(1).ttype):
                exactv.append(self.expect_expression())

        self.linebreak()

        if region == ConstantRegion.DEF and const not in self.constant_def_sequence:
            self.constant_def_sequence.append(const)
        elif (
            region == ConstantRegion.WHERE and const not in self.constant_where_sequence
        ):
            self.constant_where_sequence.append(const)
        if const not in self.constant_exacts:
            self.constant_exacts[const] = exactv
        if const not in self.constant_floats:
            self.constant_floats[const] = float(floatv)

    # where_block := WHERE: constant_block
    def where_block(self):
        t1 = self.lexer.peek(1)
        t2 = self.lexer.peek(2)
        if (
            t1.ttype == TokenType.NAME
            and t1.lexeme == "WHERE"
            and t2.ttype == TokenType.COLON
        ):
            self.expect(TokenType.NAME)
            self.expect(TokenType.COLON)
            self.constant_block(ConstantRegion.WHERE)

    # value := -? [name|int|float]
    def value(self) -> list[Token]:
        token_list = []
        if self.lexer.peek(1).ttype == TokenType.MINUS:
            token_list.append(self.expect(TokenType.MINUS))

        ttype = self.lexer.peek(1).ttype
        match ttype:
            case TokenType.NAME:
                token_list.append(self.expect(TokenType.NAME))
            case TokenType.INT:
                token_list.append(self.expect(TokenType.INT))
            case TokenType.FLOAT:
                token_list.append(self.expect(TokenType.FLOAT))
            case _:
                self.syntax_error()
        return token_list

    # vertex_def := name = (value, value, value) \n
    def vertex_def(self):
        token_list = []
        name = self.expect(TokenType.NAME).lexeme
        self.expect(TokenType.EQ)
        self.expect(TokenType.LPAREN)
        token_list.append(Token(TokenType.LSQUARE, None, -1, -1, -1))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        self.expect(TokenType.RPAREN)
        token_list.append(Token(TokenType.RSQUARE, None, -1, -1, -1))
        self.linebreak()

        self.vertices[name] = token_list

    # face_def := { [int,]* int } \n
    def face_def(self):
        face = []
        self.expect(TokenType.LBRACE)
        while (
            self.lexer.peek(1).ttype == TokenType.INT
            and self.lexer.peek(2).ttype == TokenType.COMMA
        ):
            face.append(self.expect(TokenType.INT).lexeme)
            self.expect(TokenType.COMMA)
        face.append(self.expect(TokenType.INT).lexeme)
        self.expect(TokenType.RBRACE)
        self.linebreak()

        self.faces.append(face)

    # constant_block := constant_def*
    def constant_block(self, region: ConstantRegion):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        t3 = self.lexer.peek(3).ttype
        t4 = self.lexer.peek(4).ttype
        t5 = self.lexer.peek(5).ttype
        t6 = self.lexer.peek(6).ttype
        while (
            t1 == TokenType.NAME
            and t2 == TokenType.EQ
            and (t3 == TokenType.FLOAT or self.is_expression_ttype(t3))
            and (
                t4 == TokenType.EQ
                or t4 == TokenType.NEWLINE
                or self.is_expression_ttype(t4)
            )
            and (
                t5 == TokenType.NAME
                or t5 == TokenType.NEWLINE
                or self.is_expression_ttype(t5)
            )
            and (
                t6 == TokenType.NAME
                or t6 == TokenType.NEWLINE
                or t6 == TokenType.EQ
                or self.is_expression_ttype(t6)
            )
        ):
            self.constant_def(region)
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype
            t3 = self.lexer.peek(3).ttype
            t4 = self.lexer.peek(4).ttype
            t5 = self.lexer.peek(5).ttype
            t6 = self.lexer.peek(6).ttype

    # vertex_block := vertex_def*
    def vertex_block(self):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        while t1 == TokenType.NAME and t2 == TokenType.EQ:
            self.vertex_def()
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype

    # face_block := Faces : \n face_def*
    def face_block(self):
        if not self.expect(TokenType.NAME).lexeme == "Faces":
            self.syntax_error()
        self.expect(TokenType.COLON)
        self.linebreak()
        while self.lexer.peek(1).ttype == TokenType.LBRACE:
            self.face_def()

    # polyhedron := name_def constant_block vertex_block face_block EOF
    def parse(self, options: GlobalOptions) -> Polyhedron:
        self.name_def()
        self.constant_block(ConstantRegion.DEF)
        self.where_block()
        self.vertex_block()
        self.face_block()
        self.expect(TokenType.EOF)

        self.constant_sequence = (
            self.constant_where_sequence + self.constant_def_sequence
        )

        faces = [[int(v) for v in f] for f in self.faces]

        return VisualPolyhedron(
            self.name,
            self.vertices,
            faces,
            self.constant_exacts,
            self.constant_floats,
            self.constant_sequence,
            options=options,
        )

    def dump_tokenstream(self):
        while self.lexer.peek(1).ttype != TokenType:
            tok = self.lexer.get()
            print(tok.ttype, tok.lexeme)


# ┌───────────────────────────────────────────────────────────────────────────┐
# │ main() and helpers                                                        │
# └───────────────────────────────────────────────────────────────────────────┘


def get_parser(filepath: str):
    if filepath.lower().endswith(".stl"):
        return StlParser(filepath)
    else:
        with open(filepath) as f:
            return VisualPolyhedraParser(f.read())


def call_openscad(polyhedron: Polyhedron, options: GlobalOptions):
    openscad_args = OpenscadArgs(polyhedron, options)
    command = ["openscad"] + openscad_args.to_openscad_args() + ["scad/interface.scad"]
    print(command)
    polyhedron.print_offset_edge_lengths()
    subprocess.run(command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="Directory containing polyhedron files")
    parser.add_argument("--file", "-f", help="Specific file to process")

    parser.add_argument("--edge-diameter", type=float, help="Diameter of edge struts")
    parser.add_argument(
        "--diameter-tolerance-fit",
        type=float,
        help="Additional tolerance added to interior diameter of generated vertex holders",
    )
    parser.add_argument(
        "--diameter-taper-fit",
        type=float,
        help="Interior diameter of generated vertex holders decrease by this amount towards their bases",
    )
    parser.add_argument(
        "--wall-thickness", type=float, help="Vertex holder wall thickness"
    )
    parser.add_argument("--radius", type=float, help="Radius of your solid")
    parser.add_argument(
        "--rod-inset", type=float, help="Vertex holders will inset edges by this amount"
    )
    parser.add_argument(
        "--global-offset",
        type=float,
        help="If --offset-type is global, then set all offsets to this value",
    )
    parser.add_argument(
        "--min-printer-overhang-angle",
        type=float,
        help="Minimum printer overhang angle",
    )
    parser.add_argument(
        "--vertex-type",
        choices=["tubular", "conical"],
        help="Tubular vertices require less material. Conical vertices are bulky but strong.",
    )
    parser.add_argument(
        "--offset-type",
        choices=["per_solid", "global", "per_vertex", "per_half_edge"],
        help="Offset type. Best computes an identical offset for each vertex in your solid. "
        "Local computes a unique offset for each vertex. Global sets all offsets to the value of "
        "--global-offset",
    )
    parser.add_argument(
        "--object-type",
        choices=["vertex_holder", "solid", "all_vertex_holders"],
        help="Object type",
    )
    parser.add_argument(
        "--group-identical-vertices",
        action="store_true",
        help="Group vertices that are equivalent under rotations",
    )
    parser.add_argument("--index")
    parser.add_argument("--colors", nargs="+", help="Color scheme for previews")
    parser.add_argument(
        "--label-vertices",
        action="store_true",
        help="Label vertices in output",
    )
    parser.add_argument(
        "--tubular-supports",
        action="store_true",
        help="Enable tubular supports",
    )
    parser.add_argument(
        "--isotropize",
        action="store_true",
        help="Enable isotropic remeshing",
    )

    args = parser.parse_args()
    options_dict = {
        "edge_diameter": args.edge_diameter,
        "diameter_tolerance_fit": args.diameter_tolerance_fit,
        "diameter_taper_fit": args.diameter_taper_fit,
        "wall_thickness": args.wall_thickness,
        "radius": args.radius,
        "rod_inset": args.rod_inset,
        "global_offset": args.global_offset,
        "min_printer_overhang_angle": args.min_printer_overhang_angle,
        "vertex_type": args.vertex_type,
        "offset_type": args.offset_type,
        "object_type": args.object_type,
        "by_tag": args.group_identical_vertices,
        "index": args.index,
        "colors": args.colors,
        "label_vertices": args.label_vertices,
        "tubular_supports": args.tubular_supports,
    }
    options_dict = {k: v for k, v in options_dict.items() if v is not None}
    if "vertex_type" in options_dict:
        options_dict["vertex_type"] = VertexType(options_dict["vertex_type"])
    if "offset_type" in options_dict:
        options_dict["offset_type"] = OffsetType(options_dict["offset_type"])
    if "object_type" in options_dict:
        options_dict["object_type"] = ObjectType(options_dict["object_type"])
    options = GlobalOptions(**options_dict)

    if args.file:
        p = get_parser(args.file)
        polyhedron = p.parse(options)
        polyhedron.isotropize()
        call_openscad(polyhedron, options)
    else:
        for filepath in glob.glob(os.path.join(args.directory, "*.txt")):
            p = get_parser(filepath)
            polyhedron = p.parse(options)
            if args.isotropize:
                polyhedron.isotropize()
                print(polyhedron.openscad())


if __name__ == "__main__":
    main()
