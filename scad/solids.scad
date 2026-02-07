use <constants.scad>
include <geometry.scad>

// Main Function: Returns a list of distinct standardized vertex figures
function get_standardized_vertex_figures(vertices, edges) =
    let(
        // 1. Build Adjacency and Raw Figures
        raw_figs = [
            for(i=[0:len(vertices)-1])
            let(
                // Find neighbors for vertex i
                neighbors = [for(e=edges) if(e[0]==i) e[1] else if(e[1]==i) e[0]],
                // Create unit vectors
                vecs = [for(n=neighbors) _vf_normalize(vertices[n] - vertices[i])]
            ) vecs
        ],
        // 2. Compute Signatures for Deduplication
        // We tag each figure with a signature [sig, figure]
        tagged = [for(f=raw_figs) [_vf_signature(f), f]],

        // 3. Sort by Signature to group identicals
        sorted_tagged = _vf_sort(tagged),

        // 4. Filter Unique Figures
        unique_figs = _vf_dedupe(sorted_tagged),

        // 5. Standardize Orientation (Mean -> Y Axis)
        std_figs = [for(f=unique_figs) _vf_standardize(f)]
    )
    std_figs;

// Vector Normalization
function _vf_normalize(v) = v / (norm(v)==0 ? 1 : norm(v));

// List Summation (Vector sum)
function _vf_sum_vecs(list, i=0) =
    i >= len(list) ? [0,0,0] : list[i] + _vf_sum_vecs(list, i+1);

// Quicksort (works for lists of numbers or lists of lists)
function _vf_sort(l) = len(l)<=1 ? l :
    let(pivot=l[floor(len(l)/2)])
    concat(
        _vf_sort([for(i=l) if(i<pivot) i]),
        [for(i=l) if(i==pivot) i],
        _vf_sort([for(i=l) if(i>pivot) i])
    );

// Generate a rotation-invariant signature for a set of vectors
// Includes sorted dot products (shape) and triple products (chirality)
function _vf_signature(vecs) =
    let(
        precision = 100000,
        n = len(vecs),
        // All pairwise dot products
        dots = _vf_sort([
            for(i=[0:n-1])
            for(j=[i:n-1])
                round((vecs[i] * vecs[j]) * precision)
        ]),
        // All triple products (Determinants) to detect mirror images
        triples = _vf_sort([
            for(i=[0:n-1])
            for(j=[0:n-1])
            for(k=[0:n-1])
                round((cross(vecs[i], vecs[j]) * vecs[k]) * precision)
        ])
    )
    concat(dots, triples);

// Deduplicate a sorted list of [signature, figure] pairs
function _vf_dedupe(list, i=0) =
    i >= len(list) ? [] :
    i == 0 ? concat([list[0][1]], _vf_dedupe(list, i+1)) :
    list[i][0] == list[i-1][0] ? _vf_dedupe(list, i+1) : // Skip duplicate
    concat([list[i][1]], _vf_dedupe(list, i+1));

// Convert Rodrigues rotation matrix to Euler angles (XYZ convention)
function rodrigues_to_euler(R) =
    let(
        // Clamp to avoid numerical issues with asin
        sin_beta = -R[2][0],
        beta = asin(sin_beta > 1 ? 1 : (sin_beta < -1 ? -1 : sin_beta)),
        cos_beta = sqrt(1 - sin_beta*sin_beta)
    )
    (abs(cos_beta) < 1e-9) ?
        // Gimbal lock at poles
        [atan2(-R[1][2], R[1][1]), beta, 0] :
        let(
            alpha = atan2(R[1][0], R[0][0]),
            gamma = atan2(R[2][1], R[2][2])
        )
        [alpha, beta, gamma];

// Standardize: Rotate vectors so their mean aligns with [0, 1, 0]
function _vf_standardize(vecs) =
    let(
        mean = _vf_sum_vecs(vecs),
        target = [0, 1, 0],
        nm = norm(mean)
    )
    (nm < 1e-9) ? vecs : // Mean is zero (e.g. balanced star), cannot align unique axis
    let(
        u_mean = mean / nm,
        axis = cross(u_mean, target),
        len_axis = norm(axis),
        dot_val = u_mean * target
    )
    (len_axis < 1e-6) ? 
        // Already aligned or anti-aligned
        (dot_val > 0 ? vecs : [for(v=vecs) [v[0], -v[1], -v[2]]]) : // Flip 180 X if anti-aligned
        let(
            // Construct Rodrigues rotation matrix
            u = axis / len_axis,
            c = dot_val,
            s = len_axis,
            C = 1-c,
            R = [
                [c + u[0]*u[0]*C,     u[0]*u[1]*C - u[2]*s, u[0]*u[2]*C + u[1]*s],
                [u[1]*u[0]*C + u[2]*s, c + u[1]*u[1]*C,     u[1]*u[2]*C - u[0]*s],
                [u[2]*u[0]*C - u[1]*s, u[2]*u[1]*C + u[0]*s, c + u[2]*u[2]*C]
            ],
            euler = rodrigues_to_euler(R)
        )
        [for(v=vecs) R * v];


// tetrahedron();
// disdyakis_triacontahedron();
figs = get_standardized_vertex_figures(disdyakis_triacontahedron_vertices, disdyakis_triacontahedron_edges);

// Visualize the result
for(i=[0:len(figs)-1]) {
    translate([i*3, 0, 0]) {
        // Draw Origin
        color("red") sphere(0.1);
        // Draw Vectors
        for(v = figs[i]) {
            color("blue")
            hull() {
                sphere(0.05);
                translate(v) sphere(0.05);
            }
        }
    }
}
#unit_sphere();
