use <solids.scad>
include <geometry.scad>


EDGE_DIAMETER = 5;
WALL_THICKNESS = 2;
EDGE_LENGTH = 200;
TUBE_DEPTH = 20;

function direction_to_euler(v) =
    [
        0,
        atan2(norm([v[0], v[1]]), v[2]),
        atan2(v[1], v[0])
    ];

module vertex_holders() {
    figs = annotated_vertex_figures(disdyakis_triacontahedron_vertices, disdyakis_triacontahedron_edges);

    colors = ["red", "green", "blue"];

    // Visualize the result
    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(EDGE_LENGTH * vertex) {
            // Draw Origin
            color(colors[tag]) sphere(0.1);
            // Draw Vectors
            rotate(euler)
            color(colors[tag])
            if (tag == 0) {
                disdyakis_triacontahedron_4(std);
            } else if (tag == 1) {
                disdyakis_triacontahedron_6(std);
            } else if (tag == 2) {
                disdyakis_triacontahedron_10(std);
            };
        }
    }
}

module disdyakis_triacontahedron_10(vecs) {
    for(v=vecs) {
        let (
            v0 = vecs[0],
            v1 = vecs[1],
            oset = EDGE_DIAMETER * norm(v0+v1) / norm(v0-v1) / 2,
            rotation = direction_to_euler(v)
        )
        translate(oset * v)
        rotate(rotation)
        linear_extrude(TUBE_DEPTH)
        difference() {
            circle(d=EDGE_DIAMETER+WALL_THICKNESS*2);
            circle(d=EDGE_DIAMETER);
        }
    }
}

module disdyakis_triacontahedron_6(vecs) {
}

module disdyakis_triacontahedron_4(vecs) {
}

//vertex_holders();
figs = annotated_vertex_figures(disdyakis_triacontahedron_vertices, disdyakis_triacontahedron_edges);
disdyakis_triacontahedron_10(figs[61][1], $fn=60);
