use <annotated_vertex_figures.scad>
include <geometry.scad>
include <constants.scad>


// Convert a unit vector to euler angles
function direction_to_euler(v) =
    [
        0,
        atan2(norm([v[0], v[1]]), v[2]),
        atan2(v[1], v[0])
    ];

// Height to translate the vertex holder before making the xy cut
function cutoff_height(v, l, r) = (l * v[2] - r * norm([v[0], v[1]])) / norm(v);

// Calculates the smallest translation length l such that the outer cylinders (radius R)
// just touch the inner cylinders (radius r).
function axis_offset(v0, v1, R, r) =
    let(
        c = v0 * v1,
        s = norm(cross(v0, v1)),

        // Mode 1: Rim of outer contacts side of inner (active for acute angles)
        l_side = (R * c + r) / s,

        // Mode 2: Rim of inner touches base of outer (active for obtuse angles)
        // Uses identity cot(theta/2) = (1 + cos theta) / sin theta
        l_base = (r * (1 + c)) / s
    )
    // Handle parallel case to avoid division by zero
    s < 1e-9 ? (c > 0 ? 1e9 : 0) :
    max(l_side, l_base);


// Dot product
function dot(a, b) = a[0]*b[0] + a[1]*b[1] + a[2]*b[2];

// Find the vector most aligned with -z (lowest vector)
function lowest_vector(vecs) =
    let(
        z_components = [for(v=vecs) v[2]],
        min_z = min(z_components),
        min_idx = search(min_z, z_components)[0]
    )
    vecs[min_idx];

// Return a pair of vectors with minimum cosine distance between them
function min_cos_dist_pair(vecs) =
    let(
        n = len(vecs),
        pairs = [for(i=[0:n-2]) for(j=[i+1:n-1]) [i, j, abs(dot(vecs[i], vecs[j]) / (norm(vecs[i]) * norm(vecs[j])))]],
        ix = search(min([for(p=pairs) p[2]]), [for(p=pairs) p[2]])[0]
    )
    [vecs[pairs[ix][0]], vecs[pairs[ix][1]]];

function offset_from_vecs(vecs) =
    let (
        pair = min_cos_dist_pair(vecs),
        v0 = pair[0],
        v1 = pair[1]
    )
    axis_offset(v0, v1, EDGE_DIAMETER/2+WALL_THICKNESS, EDGE_DIAMETER/2);

function best_offset(figs) =
    let (
        offsets = [for(i=[0:len(figs)-1])
            let ( std = figs[i][1] )
            offset_from_vecs(std)
        ],
        best = max(offsets)
    )
    best;

module vertex_holder(vecs, oset=0) {
    cutoff = cutoff_height(lowest_vector(vecs), oset, EDGE_DIAMETER/2+WALL_THICKNESS);

    difference() {
        for(v=vecs) {
            rotation = direction_to_euler(v);
            translate(oset * v)
            rotate(rotation)
            union() {
                linear_extrude(TUBE_DEPTH)
                difference() {
                    circle(d=EDGE_DIAMETER+WALL_THICKNESS*2);
                    circle(d=EDGE_DIAMETER);
                }
                translate([0, 0, -oset])
                cylinder(d=EDGE_DIAMETER+WALL_THICKNESS*2, h=WALL_THICKNESS+oset);
            }
        }
        translate([0, 0, -50+cutoff])
        cube([100, 100, 100], center=true);
    }
}

module conical_vertex_holder(vecs, oset=0) {
    cutoff = cutoff_height(lowest_vector(vecs), oset, EDGE_DIAMETER/2+WALL_THICKNESS);

    difference() {
        hull() {
            for(v=vecs) {
                rotation = direction_to_euler(v);
                translate(oset * v)
                rotate(rotation)
                translate([0, 0, -oset])
                linear_extrude(TUBE_DEPTH+oset)
                circle(d=EDGE_DIAMETER+WALL_THICKNESS*2);
            }
        }
        for (v=vecs) {
            rotation = direction_to_euler(v);
            translate(oset * v)
            rotate(rotation)
            translate([0, 0, WALL_THICKNESS])
            linear_extrude(TUBE_DEPTH)
            circle(d=EDGE_DIAMETER);
        }
        translate([0, 0, -50+cutoff])
        cube([100, 100, 100], center=true);
    }
}

module all_vertex_holders(vertices, edges, type="tubular", oset="best") {
    figs = annotated_vertex_figures(vertices, edges);
    holder_offset =
        oset == "best" ? best_offset(figs) :
        oset == "global" ? GLOBAL_CATALAN_OFFSET :
        GLOBAL_CATALAN_OFFSET;
    colors = ["red", "green", "blue"];

    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(RADIUS * [i, 0, 0])
        color(colors[tag])
        if (type == "tubular") {
            vertex_holder(std, holder_offset);
        } else if (type == "conical") {
            conical_vertex_holder(std, holder_offset);
        }
    }
}



module one_vertex_holder(vertices, edges, tag, type="tubular", oset="best") {
    figs = annotated_vertex_figures(vertices, edges);
    holder_offset =
        oset == "best" ? best_offset(figs) :
        oset == "global" ? GLOBAL_CATALAN_OFFSET :
        GLOBAL_CATALAN_OFFSET;
    colors = ["red", "green", "blue"];

    // Filter to find the indices of all figures where tag == 1
    matches = [for (i = [0:len(figs)-1]) if (figs[i][4] == tag) i];

    // Only proceed if at least one match was found
    if (len(matches) > 0) {
        // Select the index of the *first* match found
        i = matches[0];
        // Extract data for that specific index
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4]; // This is guaranteed to be 1

        color(colors[tag])
        if (type == "tubular") {
            vertex_holder(std, holder_offset);
        } else if (type == "conical") {
            conical_vertex_holder(std, holder_offset);
        }
    }
}

one_vertex_holder(rhombic_dodecahedron_vertices, rhombic_dodecahedron_edges, 0, type="conical", oset="best", $fn=60);
