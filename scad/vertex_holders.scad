use <annotated_vertex_figures.scad>
include <geometry.scad>
include <constants.scad>


// Locus of lowest points along a cylinder. v is axis, r is radius, l is parameter
function lowest_line_on_cylinder(v, l, r) =
    let(
        uv = v / norm(v),
        center = uv * l,
        down = [0, 0, -1],
        proj = down - (down * uv) * uv
    )
    (norm(proj) < 1e-9)
        ? center + [r, 0, 0]
        : center + r * (proj / norm(proj));

// Convert a unit vector to euler angles
function direction_to_euler(v) =
    [
        0,
        atan2(norm([v[0], v[1]]), v[2]),
        atan2(v[1], v[0])
    ];


// Height to translate the vertex holder before making the xy cut
function cutoff_height(v, l, r) =
    v.z >= 0 ?
        lowest_line_on_cylinder(v, l, r).z:
        lowest_line_on_cylinder(v, l+TUBE_DEPTH, r).z;


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


// Find the vector most aligned with -z (lowest vector)
function lowest_vector(vecs) =
    let(
        z_components = [for(v=vecs) v[2]],
        min_z = min(z_components),
        min_ix = search(min_z, z_components)[0]
    )
    min_ix;

// Return the vector with minimum cosine distance to t; assume that t = vecs[0]
function min_cos_dist(index, vecs) =
    let (
        scores = [for(i=[1:len(vecs)-1])
            i == index ?
                -1000 :
                (vecs[index] * vecs[i]) / norm(vecs[i])],
        ix = search(max(scores), scores)[0]
    )
    vecs[ix+1];

function offset_from_single_vec(index, vecs) =
    let ( closest = min_cos_dist(index, vecs) )
    axis_offset(vecs[index], closest, OUTER_TUBE_RADIUS, EDGE_DIAMETER/2);

module tubular_vertex_holder(vecs, offsets=[]) {
    offsets = len(offsets) == 0 ?
        [for (i=[0:len(vecs)-1]) offset_from_single_vec(i, vecs)] :
        offsets;

    vertex_offset = max(offsets);

    scaled_vecs = [for (i=[0:len(vecs)-1]) vecs[i] * (offsets[i] + TUBE_DEPTH)];
    lowest_scaled_vec_ix = lowest_vector(scaled_vecs);

    cutoff = cutoff_height(
        vecs[lowest_scaled_vec_ix],
        offsets[lowest_scaled_vec_ix],
        OUTER_TUBE_RADIUS);

    difference() {
        for(i=[0:len(vecs)-1]) {
            v = vecs[i];
            rotation = direction_to_euler(v);
            half_edge_offset = offsets[i];

            // Add support structure if v sits below the minimum overhang angle
            if (rotation[1] > MIN_PRINTER_OVERHANG_ANGLE) {
                lowest_top_point = lowest_line_on_cylinder(
                    v,
                    half_edge_offset+TUBE_DEPTH,
                    OUTER_TUBE_RADIUS);

                base_inset =
                    abs(lowest_top_point.z - cutoff) 
                    / tan(MIN_PRINTER_OVERHANG_ANGLE);

                clamped_base_position = min(
                    max(half_edge_offset + TUBE_DEPTH - base_inset, 0),
                    norm([lowest_top_point.x, lowest_top_point.y]));

                tube_top_to_cutoff_plane =
                    -OUTER_TUBE_RADIUS
                    -lowest_top_point.z
                    +cutoff
                    +(half_edge_offset+TUBE_DEPTH)*v.z;
                hull() {
                    // First, move endpoint to tube length.
                    // Then move endpoint inwards along xy axes by base_inset, to give nice overhangs instead of straight drops
                    // Clamp endpoint to 0, so as not to move in the opposite direction of v
                    translate(clamped_base_position * [v.x, v.y, 0])
                    // Move endpoint downwards to cutoff plane
                    translate([0, 0, tube_top_to_cutoff_plane])
                    rotate(rotation)
                    cube([0.1, OUTER_TUBE_RADIUS, 0.1], center=true);

                    translate([0, 0, tube_top_to_cutoff_plane])
                    rotate(rotation)
                    cube([0.1, OUTER_TUBE_RADIUS, 0.1], center=true);


                    translate(half_edge_offset * v)
                    rotate(rotation)
                    difference() {
                        union() {
                            cylinder(r=OUTER_TUBE_RADIUS, h=TUBE_DEPTH);
                            translate([0, 0, -half_edge_offset])
                            cylinder(r=OUTER_TUBE_RADIUS, h=WALL_THICKNESS+half_edge_offset);
                        }
                        translate([-50+(EDGE_DIAMETER+DIAMETER_TOLERANCE_FIT)/2, 0, 0])
                        cube([100, 100, 100], center=true);
                    }
                }
            }

            // Tubes
            translate(half_edge_offset * v)
            rotate(rotation)
            union() {
                cylinder(r=OUTER_TUBE_RADIUS, h=TUBE_DEPTH);
                translate([0, 0, -half_edge_offset])
                cylinder(r=OUTER_TUBE_RADIUS, h=WALL_THICKNESS+half_edge_offset);
            }
        }

        for(i=[0:len(vecs)-1]) {
            v = vecs[i];
            rotation = direction_to_euler(v);
            half_edge_offset = offsets[i];
            translate(half_edge_offset * v)
            rotate(rotation)
            // A tiny offset is added to the length of the internal cylinder
            // to prevent z-fighting on the top surface
            cylinder(
                d1=EDGE_DIAMETER+DIAMETER_TOLERANCE_FIT-DIAMETER_TAPER_DECREASE,
                d2=EDGE_DIAMETER+DIAMETER_TOLERANCE_FIT,
                h=TUBE_DEPTH+0.01);
        }

        // Flat bottom plane
        translate([0, 0, -50+cutoff])
        cube([100, 100, 100], center=true);
    }
}

module conical_vertex_holder(vecs, offsets=[]) {
    // If no offset is specified, select a local offset
    vertex_offset = (len(offsets) == 0) ? offset_from_vecs(vecs): max(offsets);
    cutoff = cutoff_height(lowest_vector(vecs), vertex_offset, OUTER_TUBE_RADIUS);

    difference() {
        hull() {
            for(v=vecs) {
                rotation = direction_to_euler(v);
                translate(vertex_offset * v)
                rotate(rotation)
                translate([0, 0, -vertex_offset])
                linear_extrude(TUBE_DEPTH+vertex_offset)
                circle(r=OUTER_TUBE_RADIUS);
            }
        }
        for (v=vecs) {
            rotation = direction_to_euler(v);
            translate(vertex_offset * v)
            rotate(rotation)
            translate([0, 0, WALL_THICKNESS])
            cylinder(
                d1=EDGE_DIAMETER+DIAMETER_TOLERANCE_FIT-DIAMETER_TAPER_DECREASE,
                d2=EDGE_DIAMETER+DIAMETER_TOLERANCE_FIT,
                h=TUBE_DEPTH);
        }
        translate([0, 0, -50+cutoff])
        cube([100, 100, 100], center=true);
    }
}

module all_vertex_holders(vertices, edges, tag, type="tubular", oset="best") {
    figs = annotated_vertex_figures(vertices, edges);
    vertex_figures = [for (i=[0:len(figs)-1]) figs[i][1]];
    holder_offset =
        OFFSET_TYPE == "per_solid" ? best_offset(vertex_figures) :
        OFFSET_TYPE == "global" ? GLOBAL_CATALAN_OFFSET :
        OFFSET_TYPE == "per_vertex" ? 0 :
        OFFSET_TYPE == "per_half_edge" ? -1 :
        GLOBAL_OFFSET;

    colors = ["red", "blue", "green"];

    for(i=[0:len(figs)-1]) {
        fig = figs[i][0];
        std = figs[i][1];
        euler = figs[i][2];
        vertex = figs[i][3];
        tag = figs[i][4];

        translate(RADIUS * [i, 0, 0])
        color(colors[tag])
        if (type == "tubular") {
            tubular_vertex_holder(std, holder_offset);
        } else if (type == "conical") {
            conical_vertex_holder(std, holder_offset);
        }
    }
}



module one_vertex_holder(vertices, edges, tag, type="tubular", oset="best") {
    figs = annotated_vertex_figures(vertices, edges);
    vertex_figures = [for (i=[0:len(figs)-1]) figs[i][1]];
    holder_offset =
        OFFSET_TYPE == "per_solid" ? best_offset(vertex_figures) :
        OFFSET_TYPE == "global" ? GLOBAL_CATALAN_OFFSET :
        OFFSET_TYPE == "per_vertex" ? 0 :
        OFFSET_TYPE == "per_half_edge" ? -1 :
        GLOBAL_OFFSET;

    colors = ["red", "blue", "green"];

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
            tubular_vertex_holder(std);
        } else if (type == "conical") {
            conical_vertex_holder(std);
        }
    }
}

one_vertex_holder(cuboctahedron_vertices, cuboctahedron_edges, 1, type="tubular", oset="best", $fn=60);
