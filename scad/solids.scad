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
