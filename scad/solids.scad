use <annotated_vertex_figures.scad>
use <vertex_holders.scad>
include <geometry.scad>
include <constants.scad>

// Create a cylinder between two points 'a' and 'b' with radius 'r'.
// Optionally, offset cylinder inward by 'o'.
module edge(a, b, d, o=0) {
    v = b - a;
    dist = norm(v);
    u = v / dist;
    a_new = a + u * o;
    h = dist - 2 * o;

    translate(a_new)
    rotate([0, acos(v.z/h), atan2(v.y, v.x)])
    cylinder(h = h, d = d, $fn = 32);
}

module hedron(coordinates, edges, norm_dist) {
    for (edge = edges) {
        a = coordinates[edge[0]] * norm_dist;
        b = coordinates[edge[1]] * norm_dist;
        edge(a, b, EDGE_DIAMETER);
    }
}

module unit_sphere() {
    sphere(r=UNIT);
}

function max_dist(v) = max([for(i=v) norm(i)]);
function arg_max_dist(v) = let(d=[for(i=v) norm(i)]) v[search(max(d), d)[0]];

module vertex_only_hedron(vertices, edges) {
    figs = annotated_vertex_figures(vertices, edges);

    norm_dist = EDGE_LENGTH / max_dist(vertices);
    hedron(vertices, edges, norm_dist);

    colors = ["red", "green", "blue"];

    // Visualize the result
    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(norm_dist * vertex) {
            // Draw Origin
            color(colors[tag]) sphere(0.1);
            // Draw Vectors
            rotate(euler)
            color(colors[tag])
            vertex_holder(std);
        }
    }
}


catalans = [
   [triakis_tetrahedron_vertices,             triakis_tetrahedron_edges],
   [rhombic_dodecahedron_vertices,            rhombic_dodecahedron_edges],
   [triakis_octahedron_vertices,              triakis_octahedron_edges],
   [tetrakis_hexahedron_vertices,             tetrakis_hexahedron_edges],
   // [deltoidal_icositetrahedron_vertices,      deltoidal_icositetrahedron_edges],
   [disdyakis_dodecahedron_vertices,          disdyakis_dodecahedron_edges],
   [pentagonal_icositetrahedron_laevo_vertices, pentagonal_icositetrahedron_laevo_edges],
   [rhombic_triacontahedron_vertices,         rhombic_triacontahedron_edges],
   [triakis_icosahedron_vertices,             triakis_icosahedron_edges],
   [pentakis_dodecahedron_vertices,           pentakis_dodecahedron_edges],
   [deltoidal_hexecontahedron_vertices,       deltoidal_hexecontahedron_edges],
   [disdyakis_triacontahedron_vertices,       disdyakis_triacontahedron_edges],
   // [pentagonal_hexecontahedron_vertices,      pentagonal_hexecontahedron_edges],
];


for (i = [0:len(catalans)-1]) {
    catalan = catalans[i];
    translate(1000 * i * [1, 0, 0]) {
        vertex_only_hedron(catalan[0], catalan[1]);
    }
}
