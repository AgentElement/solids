use <annotated_vertex_figures.scad>
use <vertex_holders.scad>
include <geometry.scad>
include <constants.scad>

function count_distinct(arr) =
    len(arr) == 0 ? [] :
    let(
        pivot = arr[0],
        remaining = [for (x = arr) if (abs(x - pivot) > 0.001) x],
        count = len(arr) - len(remaining)
    )
    concat(
        [[pivot, count]],
        count_distinct(remaining)
    );


module print_edge_lengths(vertices, edges, figs, oset, name="") {
    figs = annotated_vertex_figures(vertices, edges);
    norm_dist = RADIUS / max_dist(vertices);
    lengths = [for (edge = edges)
        let (
            a = vertices[edge[0]] * norm_dist,
            b = vertices[edge[1]] * norm_dist,
            v = b - a,
            dist = norm(v),
            length = dist - 2 * oset
        ) length
    ];
    distincts = count_distinct(lengths);
    for (i = [0:len(distincts)-1]) {
        pair = distincts[i];
        length = pair[0];
        count = pair[1];
        echo(str(name, "_", i), length, count, oset);
    }
}

// Create a cylinder between two points 'a' and 'b' with radius 'r'.
// Optionally, offset cylinder inward by 'o'. Echo the length + name
module edge(a, b, d, o=0) {
    v = b - a;
    dist = norm(v);
    length = dist - 2 * o;
    if (dist > 2 * o) {
        phi = atan2(v[1], v[0]);
        theta = acos(v[2] / dist);

        translate(a)
        rotate([0, theta, phi])
        translate([0, 0, o])
        cylinder(h = length, d = d);
    }
}

module hedron_edges(coordinates, edges, norm_dist, o=0) {
    for (edge = edges) {
        a = coordinates[edge[0]] * norm_dist;
        b = coordinates[edge[1]] * norm_dist;
        edge(a, b, EDGE_DIAMETER, o);
    }
}

module unit_sphere() {
    sphere(r=UNIT);
}

function max_dist(v) = max([for(i=v) norm(i)]);
function arg_max_dist(v) = let(d=[for(i=v) norm(i)]) v[search(max(d), d)[0]];

module hedron(vertices, edges, name="", type="tubular", oset="best") {
    figs = annotated_vertex_figures(vertices, edges);

    holder_offset =
        oset == "best" ? best_offset(figs) :
        oset == "global" ? GLOBAL_CATALAN_OFFSET :
        GLOBAL_CATALAN_OFFSET;

    norm_dist = RADIUS / max_dist(vertices);
    print_edge_lengths(vertices, edges, figs, holder_offset, name);
    hedron_edges(vertices, edges, norm_dist, holder_offset+WALL_THICKNESS);

    colors = ["red", "green", "blue"];

    // Visualize the result
    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(norm_dist * vertex)
        rotate(euler)
        color(colors[tag])
        if (type == "tubular") {
            vertex_holder(std, holder_offset);
        } else if (type == "conical") {
            conical_vertex_holder(std, holder_offset);
        }
    }
}


catalans = [
    [triakis_tetrahedron_vertices,               triakis_tetrahedron_edges,               "triakis_tetrahedron"],
    [rhombic_dodecahedron_vertices,              rhombic_dodecahedron_edges,              "rhombic_dodecahedron"],
    [triakis_octahedron_vertices,                triakis_octahedron_edges,                "triakis_octahedron"],
    [tetrakis_hexahedron_vertices,               tetrakis_hexahedron_edges,               "tetrakis_hexahedron"],
    [deltoidal_icositetrahedron_vertices,        deltoidal_icositetrahedron_edges,        "deltoidal_icositetrahedron"],
    [disdyakis_dodecahedron_vertices,            disdyakis_dodecahedron_edges,            "disdyakis_dodecahedron"],
    [pentagonal_icositetrahedron_laevo_vertices, pentagonal_icositetrahedron_laevo_edges, "pentagonal_icositetrahedron_laevo"],
    [rhombic_triacontahedron_vertices,           rhombic_triacontahedron_edges,           "rhombic_triacontahedron"],
    [triakis_icosahedron_vertices,               triakis_icosahedron_edges,               "triakis_icosahedron"],
    [pentakis_dodecahedron_vertices,             pentakis_dodecahedron_edges,             "pentakis_dodecahedron"],
    [deltoidal_hexecontahedron_vertices,         deltoidal_hexecontahedron_edges,         "deltoidal_hexecontahedron"],
    [disdyakis_triacontahedron_vertices,         disdyakis_triacontahedron_edges,         "disdyakis_triacontahedron"],
    [pentagonal_hexecontahedron_laevo_vertices,  pentagonal_hexecontahedron_laevo_edges,  "pentagonal_hexecontahedron_laevo"],
];

archimedians = [
    [truncated_tetrahedron_vertices,       truncated_tetrahedron_edges,       "truncated_tetrahedron"],
    [cuboctahedron_vertices,               cuboctahedron_edges,               "cuboctahedron"],
    [truncated_cube_vertices,              truncated_cube_edges,              "truncated_cube"],
    [truncated_octahedron_vertices,        truncated_octahedron_edges,        "truncated_octahedron"],
    [rhombicuboctahedron_vertices,         rhombicuboctahedron_edges,         "rhombicuboctahedron"],
    [truncated_cuboctahedron_vertices,     truncated_cuboctahedron_edges,     "truncated_cuboctahedron"],
    [snub_cube_laevo_vertices,             snub_cube_laevo_edges,             "snub_cube_laevo"],
    [icosidodecahedron_vertices,           icosidodecahedron_edges,           "icosidodecahedron"],
    [truncated_dodecahedron_vertices,      truncated_dodecahedron_edges,      "truncated_dodecahedron"],
    [truncated_icosahedron_vertices,       truncated_icosahedron_edges,       "truncated_icosahedron"],
    [rhombicosidodecahedron_vertices,      rhombicosidodecahedron_edges,      "rhombicosidodecahedron"],
    [truncated_icosidodecahedron_vertices, truncated_icosidodecahedron_edges, "truncated_icosidodecahedron"],
    [snub_dodecahedron_laevo_vertices,     snub_dodecahedron_laevo_edges,     "snub_dodecahedron_laevo"],
];

platonics = [
    [tetrahedron_vertices,  tetrahedron_edges,  "tetrahedron"],
    [cube_vertices,         cube_edges,         "cube"],
    [octahedron_vertices,   octahedron_edges,   "octahedron"],
    [dodecahedron_vertices, dodecahedron_edges, "dodecahedron"],
    [icosahedron_vertices,  icosahedron_edges,  "icosahedron"],
];


for (i = [0:len(catalans)-1]) {
    catalan = catalans[i];
    translate(1000 * [i, 0, 0])
        hedron(catalan[0], catalan[1], name=catalan[2]);
}

for (i = [0:len(archimedians)-1]) {
    archimedian = archimedians[i];
    translate(1000 * [i, 1, 0])
        hedron(archimedian[0], archimedian[1], name=archimedian[2]);
}

for (i = [0:len(platonics)-1]) {
    platonic = platonics[i];
    translate(1000 * [i, 2, 0])
        hedron(platonic[0], platonic[1], name=platonic[2]);
}
