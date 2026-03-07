// Main Function: Returns a list of distinct standardized vertex figures
// Returns a len(vertices) list of 5-tuples containing:
// 1. A vertex figure
// 2. A standardization of vertex figures (the figure oriented such that the
//      mean of all vectors points towards [0, 0, 1]
// 3. The euler angle triple required to convert a standardization back to its original orientation
// 4. The position of the original vertex
// 5. A tag; vertex figures invariant under rotation recieve identical tags.
function annotated_vertex_figures(vertices, edges) =
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
        signed = [
            for(i=[0:len(vertices)-1])
            let (
                fig = raw_figs[i],
                std = optimal_reorient(fig),
                tuple = [_vf_signature(fig), fig, std, vertices[i]]
            ) tuple
        ],

        // 3. Sort by Signature to group identicals
        sorted = _vf_sort(signed),

        // 4. Filter Unique Figures
        tagged = _vf_tag(sorted),

        // 5. figure, standardization, euler angle, vertex, tag
        annotated_vertex_figures = [
            for(i=[0:len(vertices)-1])
            [sorted[i][1], sorted[i][2][0], sorted[i][2][1], sorted[i][3], tagged[i]]
        ]
    )
    annotated_vertex_figures;


// Matrix transpose
function _vf_transpose(m) =
    [for (j = [0 : len(m[0]) - 1])
        [for (i = [0 : len(m) - 1]) m[i][j]]
    ];

// Guarded norm
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

// Tag a sorted list of [signature, figure] pairs
function _vf_tag(list, i=0, tag=0) =
    i >= len(list) ? [] :
    i == 0 || list[i][0] == list[i-1][0] ?
        concat(tag, _vf_tag(list, i+1, tag)) :
        concat(tag+1, _vf_tag(list, i+1, tag+1));

// Decomposes a 3x3 rotation matrix into [x, y, z] Euler angles
// suitable for OpenSCAD's rotate() function
function _vf_matrix_to_rotation(m) =
    let(
        // Calculate sy to check for Gimbal Lock (cos(y))
        sy = sqrt(m[0][0] * m[0][0] + m[1][0] * m[1][0]),
        singular = sy < 1e-6
    )
    (!singular) ?
        [
            atan2(m[2][1], m[2][2]), // x
            atan2(-m[2][0], sy),     // y
            atan2(m[1][0], m[0][0])  // z
        ]
    :
        // Handle Gimbal Lock cases
        (m[2][0] < 0) ?
            // y = 90 degrees (Singularity)
            [ atan2(-m[1][2], m[1][1]), 90, 0 ]
        :
            // y = -90 degrees (Singularity)
            [ atan2(-m[1][2], m[1][1]), -90, 0 ];

// Rotate vectors so their mean aligns with [0, 0, 1]
function mean_reorient(vecs, target=[0, 0, 1]) =
    let(
        mean = _vf_sum_vecs(vecs),
        target = [0, 0, 1],
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
        (dot_val > 0 ?
            [vecs, [0, 0, 0]] :
            [[for(v=vecs) [v[0], -v[1], -v[2]]], [180, 0, 0]]) : // Flip 180 X if anti-aligned
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
            euler = _vf_matrix_to_rotation(_vf_transpose(R))
        )
        [[for(v=vecs) R * v], euler];


function optimal_reorient(vecs) =
    let(
        R = optimal_rotation_matrix(vecs),
        euler = _vf_matrix_to_rotation(_vf_transpose(R))
    )
    [[for(v=vecs) R * v], euler];


// Let theta_xy(v) be the angle between a vector and the xy plane. This function
// produces a rotation matrix R such that the sum over v in vecs of theta_xy(R * v)
// is minimized.
function optimal_rotation_matrix(vecs) =
    let(
        // 1. Construct the scatter matrix S
        S = _orm_get_S_matrix(vecs),

        // 2. Find the smallest eigenvalue
        min_lambda = _orm_get_min_eigenvalue(S),

        // 3. Find the corresponding eigenvector (this will be our new Z axis)
        z_axis = _orm_get_eigenvector(S, min_lambda),

        // 4. Construct the other two axes to form an orthonormal basis
        // Pick a temporary vector non-parallel to z_axis
        temp_vec = (abs(z_axis[2]) > 0.9) ? [1, 0, 0] : [0, 0, 1],

        // x_axis is perpendicular to z_axis
        x_axis = _orm_normalize(cross(temp_vec, z_axis)),

        // y_axis is perpendicular to both (Right-Hand Rule)
        y_axis = _orm_normalize(cross(z_axis, x_axis))
    )
    // Return rotation matrix (rows are the new basis vecs)
    [x_axis, y_axis, z_axis];


function _orm_sum(list, idx=0, acc=0) =
    (idx >= len(list)) ? acc : _orm_sum(list, idx+1, acc+list[idx]);

function _orm_normalize(v) =
    let(l = norm(v)) (l < 1e-12) ? [0,0,0] : v / l;

function _orm_get_S_matrix(vecs) =
    let(
        // Normalize input vecs
        unit_vecs = [for(v=vecs) if(norm(v) > 1e-12) v / norm(v)],
        // If empty, return Identity-like structure (diagonal 1s)
        fallback = [[1,0,0], [0,1,0], [0,0,1]]
    )
    (len(unit_vecs) == 0) ? fallback :
    let(
        xx = _orm_sum([for(v=unit_vecs) v[0]*v[0]]),
        xy = _orm_sum([for(v=unit_vecs) v[0]*v[1]]),
        xz = _orm_sum([for(v=unit_vecs) v[0]*v[2]]),
        yy = _orm_sum([for(v=unit_vecs) v[1]*v[1]]),
        yz = _orm_sum([for(v=unit_vecs) v[1]*v[2]]),
        zz = _orm_sum([for(v=unit_vecs) v[2]*v[2]])
    )
    [[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]];

function _orm_get_min_eigenvalue(M) = 
    let(
        // Analytical solution for eigenvalues of 3x3 real symmetric matrix
        p1 = M[0][1]*M[0][1] + M[0][2]*M[0][2] + M[1][2]*M[1][2]
    )
    (p1 == 0) ? min(M[0][0], M[1][1], M[2][2]) : // Already diagonal
    let(
        q = (M[0][0] + M[1][1] + M[2][2]) / 3,
        p2 = pow(M[0][0] - q, 2) + pow(M[1][1] - q, 2) + pow(M[2][2] - q, 2) + 2 * p1,
        p = sqrt(p2 / 6),
        // Matrix B = (1/p) * (M - qI)
        B = [
            [(M[0][0]-q)/p, M[0][1]/p,     M[0][2]/p],
            [M[1][0]/p,     (M[1][1]-q)/p, M[1][2]/p],
            [M[2][0]/p,     M[2][1]/p,     (M[2][2]-q)/p]
        ],
        // Determinant of B
        r_raw = (B[0][0]*B[1][1]*B[2][2] + B[0][1]*B[1][2]*B[2][0] + B[0][2]*B[1][0]*B[2][1]
               - B[0][2]*B[1][1]*B[2][0] - B[0][1]*B[1][0]*B[2][2] - B[0][0]*B[1][2]*B[2][1]) / 2,
        r = (r_raw <= -1) ? -1 : ((r_raw >= 1) ? 1 : r_raw),
        phi = acos(r) / 3
    )
    // The eigenvalues are q + 2p*cos(phi), q + 2p*cos(phi + 120), q + 2p*cos(phi + 240).
    // Smallest eigenvalue:
    min(
        q + 2 * p * cos(phi),
        q + 2 * p * cos(phi + 120),
        q + 2 * p * cos(phi + 240)
    );

function _orm_get_eigenvector(M, lambda) =
    let(
        // M - lambda*I
        A = [
            [M[0][0]-lambda, M[0][1], M[0][2]],
            [M[1][0], M[1][1]-lambda, M[1][2]],
            [M[2][0], M[2][1], M[2][2]-lambda]
        ],
        // Cross products of rows determine the null space direction
        c0 = cross(A[0], A[1]),
        c1 = cross(A[0], A[2]),
        c2 = cross(A[1], A[2]),
        n0 = norm(c0), n1 = norm(c1), n2 = norm(c2)
    )
    // Select the non-zero cross product with largest norm for stability
    (n0 >= n1 && n0 >= n2 && n0 > 1e-6) ? c0 / n0 :
    (n1 >= n2 && n1 > 1e-6) ? c1 / n1 :
    (n2 > 1e-6) ? c2 / n2 :
    // Fallback if all cross products are zero (rank < 2)
    // Find a vector orthogonal to any non-zero row
    (norm(A[0]) > 1e-6) ? _orm_get_orthogonal(A[0]) :
    (norm(A[1]) > 1e-6) ? _orm_get_orthogonal(A[1]) :
    (norm(A[2]) > 1e-6) ? _orm_get_orthogonal(A[2]) :
    [0, 0, 1]; // Matrix is zero, return Z axis

function _orm_get_orthogonal(v) =
    let(n = _orm_normalize(v))
    (abs(n[0]) > 0.9) ? _orm_normalize(cross(n, [0, 1, 0])) 
                      : _orm_normalize(cross(n, [1, 0, 0]));
