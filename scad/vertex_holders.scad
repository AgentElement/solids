use <annotated_vertex_figures.scad>
include <geometry.scad>
include <constants.scad>

function base_length(oset, angle, height) =
    let (
        l = oset + TUBE_DEPTH,
        r = EDGE_DIAMETER/2+WALL_THICKNESS,
        theta = MAX_PRINT_OVERHANG_ANGLE,
        height_adjustment = h * (cot(angle) - cot(theta)),
        length = r > l * tan(angle) ?
            l * sin(angle) :
            (l * sin(theta-angle) + r * cos(theta-angle)) / sin(theta)
    )
    length - height_adjustment;


// angle between a vector and the xy plane
function angle_xy(v) = atan2(v.z, norm([v.x, v.y]));

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

// Return the vector with minimum cosine distance to t; assume that t = vecs[0]
function min_cos_dist(t, vecs) =
    let (
        scores = [for(i=[1:len(vecs)-1]) dot(t,vecs[i]) / norm(vecs[i])],
        ix = search(max(scores), scores)[0]
    )
    vecs[ix+1];

function offset_from_vecs(vecs) =
    let (
        v0 = vecs[0],
        v1 = min_cos_dist(v0, vecs)
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

module vertex_holder(vecs, holder_offset=0) {
    v0 = vecs[0];
    v1 = min_cos_dist(v0, vecs);
    oset = holder_offset == 0 ? axis_offset(v0, v1, EDGE_DIAMETER/2+WALL_THICKNESS, EDGE_DIAMETER/2) : holder_offset;
    rad = oset * norm([v0[0], v0[1]]);
    cutoff = cutoff_height(v0, oset, EDGE_DIAMETER/2+WALL_THICKNESS);

    // cylinder(r=rad, h=WALL_THICKNESS);
    difference() {
        for(v=vecs) {
            rotation = direction_to_euler(v);
            zrot = [0, 0, 90+rotation.z];
            angle = angle_xy(v);
            echo(angle);
            echo(oset+TUBE_DEPTH);
            echo(blen);
            blen = base_length(oset, angle);
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
            hull() {
                rotate(rotation)
                difference() {
                    cylinder(d=EDGE_DIAMETER+WALL_THICKNESS*2, h=TUBE_DEPTH+oset);
                    translate([EDGE_DIAMETER/2-50, 0, 0])
                    cube([100, 100, 100], center=true);
                }
                rotate(zrot)
                translate([0, -blen, 0])
                #cube([EDGE_DIAMETER, 0.01, 0.01], center=true);
            }
        }
        translate([0, 0, -50+cutoff])
        cube([100, 100, 100], center=true);
    }
}

// vertex_holders();

module all_vertex_holders(vertices, edges) {
    figs = annotated_vertex_figures(vertices, edges);
    holder_offset = best_offset(figs);
    colors = ["red", "green", "blue"];

    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(RADIUS * [i, 0, 0])
        color(colors[tag])
        vertex_holder(std, holder_offset);
    }
}


module one_vertex_holder(vertices, edges, tag) {
    figs = annotated_vertex_figures(vertices, edges);
    holder_offset = best_offset(figs);
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
        vertex_holder(std, holder_offset);
    }
}

one_vertex_holder(disdyakis_triacontahedron_vertices, disdyakis_triacontahedron_edges, 2, $fn=60);
