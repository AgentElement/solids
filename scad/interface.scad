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
GLOBAL_OFFSET = 7.72;
MIN_PRINTER_OVERHANG_ANGLE = 30;
OUTER_TUBE_RADIUS = EDGE_DIAMETER/2+WALL_THICKNESS;


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
eulers = [];
tags = [];
offsets = [];


module vertex_holder(holder_offset, index) {
    vertex_figure = vertex_figures[index];
    color(COLORS[index % len(COLORS)])
    if (VERTEX_TYPE == "tubular") {
        tubular_vertex_holder(vertex_figure, oset=holder_offset);
    } else if (VERTEX_TYPE == "conical") {
        conical_vertex_holder(vertex_figure, oset=holder_offset);
    }
}

module solid(holder_offset) {
    norm_dist = RADIUS / max_dist(vertices);
    hedron_edges(vertices, edges, norm_dist, holder_offset);
    for (i=[0:len(vertices)-1]) {
        vertex = vertices[i];
        vertex_figure = vertex_figures[i];
        euler = eulers[i];
        tag = tags[i];

        translate(norm_dist * vertex)
        // The python script gives rotations in radians.
        rotate(euler * 180 / PI)
        color(COLORS[tag % len(COLORS)])
        if (VERTEX_TYPE == "tubular") {
            tubular_vertex_holder(vertex_figure, oset=holder_offset);
        } else if (VERTEX_TYPE == "conical") {
            conical_vertex_holder(vertex_figure, oset=holder_offset);
        }
    }
}

module main() {
    holder_offset =
        OFFSET_TYPE == "per_solid" ? best_offset(vertex_figures) :
        OFFSET_TYPE == "global" ? GLOBAL_CATALAN_OFFSET :
        OFFSET_TYPE == "per_vertex" ? 0 :
        OFFSET_TYPE == "per_half_edge" ? -1 :
        GLOBAL_OFFSET;

    if (OBJECT == "vertex_holder") {
    index = BY_TAG ?
        [for (i = [0:len(tags)-1]) if (tags[i] == INDEX) i][0] :
        INDEX;
        vertex_holder(holder_offset, index, $fn=60);
    } else {
        solid(holder_offset);
    }
}

main();
