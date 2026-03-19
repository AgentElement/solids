use <vertex_holders.scad>
use <solids.scad>

// The python script sets all of these global variables with the -D flag
// Values here are defaults.
EDGE_DIAMETER = 3.0;
DIAMETER_TOLERANCE_FIT = 0.35;
DIAMETER_TAPER_DECREASE = 0.10;
WALL_THICKNESS = 1.2;
RADIUS = 200;
ROD_INSET = 8;
TUBE_DEPTH = ROD_INSET+WALL_THICKNESS;
MIN_PRINTER_OVERHANG_ANGLE = 30;
OUTER_TUBE_RADIUS = EDGE_DIAMETER/2+WALL_THICKNESS;
LABEL_VERTICES=true;
TUBULAR_SUPPORTS=true;


VERTEX_TYPE = "tubular";    // tubular, conical
OFFSET_TYPE = "best";       // per_half_edge, per_vertex, per_solid, global

OBJECT = "vertex_holder";   // vertex_holder, solid
BY_TAG = true;
INDEX = 0;
COLORS = ["red", "green", "blue"];

// Openscad hangs if you don't set these lists with a flag
vertices = [];
edges = [];
vertex_figures = [];
vertex_figure_edges = [];
eulers = [];
tags = [];
offsets = [];


module vertex_holder(index) {
    vertex_figure = vertex_figures[index];
    offset_array = offsets[index];
    edge_list = vertex_figure_edges[index];
    color(COLORS[index % len(COLORS)])
    if (VERTEX_TYPE == "tubular") {
        tubular_vertex_holder(vertex_figure, offset_array, edge_list);
    } else if (VERTEX_TYPE == "conical") {
        conical_vertex_holder(vertex_figure, offset_array, edge_list);
    }
}

module solid() {
    norm_dist = RADIUS / max_dist(vertices);
    hedron_edges(vertices, edges, norm_dist);
    for (i=[0:len(vertices)-1]) {
        vertex = vertices[i];
        vertex_figure = vertex_figures[i];
        offset_array = offsets[i];
        euler = eulers[i];
        tag = tags[i];

        translate(norm_dist * vertex)
        // The python script gives rotations in radians.
        rotate(euler * 180 / PI)
        color(COLORS[tag % len(COLORS)])
        if (VERTEX_TYPE == "tubular") {
            tubular_vertex_holder(vertex_figure, offset_array, vertex_figure_edges[i]);
        } else if (VERTEX_TYPE == "conical") {
            conical_vertex_holder(vertex_figure, offset_array, vertex_figure_edges[i]);
        }
    }
}

module all_vertex_holders() {
    norm_dist = RADIUS / max_dist(vertices);
    for (i=[0:len(vertices)-1]) {
        vertex = vertices[i];
        vertex_figure = vertex_figures[i];
        offset_array = offsets[i];
        euler = eulers[i];
        tag = tags[i];

        translate(i * 100 * [1, 0, 0])
        color(COLORS[tag % len(COLORS)])
        if (VERTEX_TYPE == "tubular") {
            tubular_vertex_holder(vertex_figure, offset_array, vertex_figure_edges[i]);
        } else if (VERTEX_TYPE == "conical") {
            conical_vertex_holder(vertex_figure, offset_array, vertex_figure_edges[i]);
        }
    }
}

module main() {
    if (OBJECT == "vertex_holder") {
        index = BY_TAG ?
            [for (i = [0:len(tags)-1]) if (tags[i] == INDEX) i][0] :
        INDEX;
        vertex_holder(index, $fn=60);
    } else if (OBJECT == "all_vertex_holders") {
        all_vertex_holders();
    } else {
        solid();
    }
}

main();
