use <constants.scad>
// use <00-p-tetrahedron/main.scad>
// use <29-c-disdyakis-triacontahedron/main.scad>
// use <29-c-disdyakis-triacontahedron/geometry.scad>


C0=3*(15+sqrt(5))/44;
C1=(5-sqrt(5))/2;
C2=3*(5+4*sqrt(5))/22;
C3=3*(5+sqrt(5))/10;
C4=sqrt(5);
C5=(75+27*sqrt(5))/44;
C6=(15+9*sqrt(5))/10;
C7=(5+sqrt(5))/2;
C8=3*(5+4*sqrt(5))/11;
vertices=[
[0.0,0.0,C8],
[0.0,0.0,-C8],
[C8,0.0,0.0],
[-C8,0.0,0.0],
[0.0,C8,0.0],
[0.0,-C8,0.0],
[0.0,C1,C7],
[0.0,C1,-C7],
[0.0,-C1,C7],
[0.0,-C1,-C7],
[C7,0.0,C1],
[C7,0.0,-C1],
[-C7,0.0,C1],
[-C7,0.0,-C1],
[C1,C7,0.0],
[C1,-C7,0.0],
[-C1,C7,0.0],
[-C1,-C7,0.0],
[C3,0.0,C6],
[C3,0.0,-C6],
[-C3,0.0,C6],
[-C3,0.0,-C6],
[C6,C3,0.0],
[C6,-C3,0.0],
[-C6,C3,0.0],
[-C6,-C3,0.0],
[0.0,C6,C3],
[0.0,C6,-C3],
[0.0,-C6,C3],
[0.0,-C6,-C3],
[C0,C2,C5],
[C0,C2,-C5],
[C0,-C2,C5],
[C0,-C2,-C5],
[-C0,C2,C5],
[-C0,C2,-C5],
[-C0,-C2,C5],
[-C0,-C2,-C5],
[C5,C0,C2],
[C5,C0,-C2],
[C5,-C0,C2],
[C5,-C0,-C2],
[-C5,C0,C2],
[-C5,C0,-C2],
[-C5,-C0,C2],
[-C5,-C0,-C2],
[C2,C5,C0],
[C2,C5,-C0],
[C2,-C5,C0],
[C2,-C5,-C0],
[-C2,C5,C0],
[-C2,C5,-C0],
[-C2,-C5,C0],
[-C2,-C5,-C0],
[C4,C4,C4],
[C4,C4,-C4],
[C4,-C4,C4],
[C4,-C4,-C4],
[-C4,C4,C4],
[-C4,C4,-C4],
[-C4,-C4,C4],
[-C4,-C4,-C4],
];
edges=[
[12,20],
[21,9],
[22,47],
[10,18],
[20,34],
[15,28],
[15,48],
[19,9],
[34,6],
[2,22],
[19,31],
[13,24],
[22,46],
[34,58],
[29,49],
[51,59],
[20,58],
[17,5],
[37,9],
[35,59],
[29,33],
[30,6],
[14,47],
[29,5],
[28,5],
[26,6],
[29,61],
[25,44],
[27,4],
[25,60],
[18,32],
[21,61],
[15,49],
[33,57],
[12,25],
[26,58],
[19,55],
[14,22],
[16,4],
[23,49],
[26,46],
[14,46],
[15,5],
[25,45],
[35,7],
[29,37],
[28,56],
[0,18],
[17,53],
[14,26],
[28,8],
[28,60],
[21,37],
[29,53],
[22,55],
[37,61],
[18,30],
[47,55],
[33,9],
[16,24],
[15,23],
[26,34],
[12,3],
[24,50],
[10,38],
[44,60],
[16,27],
[23,56],
[2,23],
[13,25],
[0,8],
[0,6],
[39,55],
[10,23],
[16,51],
[49,57],
[18,54],
[12,42],
[11,39],
[23,41],
[11,23],
[10,2],
[24,42],
[25,52],
[19,33],
[1,19],
[31,7],
[52,60],
[36,60],
[36,8],
[40,56],
[21,7],
[38,54],
[26,30],
[29,57],
[13,21],
[27,7],
[12,24],
[19,39],
[20,42],
[27,47],
[12,44],
[18,38],
[30,54],
[21,35],
[26,50],
[21,59],
[23,40],
[26,54],
[21,45],
[27,51],
[24,3],
[18,56],
[28,48],
[10,40],
[23,57],
[18,8],
[18,6],
[27,35],
[29,9],
[27,59],
[21,43],
[26,4],
[14,4],
[28,36],
[11,19],
[1,7],
[22,39],
[43,59],
[17,29],
[24,43],
[50,58],
[11,2],
[22,54],
[11,41],
[10,22],
[20,44],
[27,31],
[20,60],
[20,6],
[20,8],
[0,20],
[25,61],
[23,48],
[11,22],
[28,32],
[17,52],
[53,61],
[16,26],
[28,52],
[19,7],
[32,56],
[17,25],
[31,55],
[15,29],
[13,3],
[32,8],
[19,57],
[14,27],
[48,56],
[16,50],
[1,9],
[17,28],
[46,54],
[45,61],
[18,40],
[41,57],
[13,45],
[24,51],
[19,41],
[20,36],
[25,53],
[22,38],
[25,3],
[13,43],
[27,55],
[24,58],
[42,58],
[24,59],
[1,21],
];

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

// --- Helper Functions ---

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
            ]
        )
        [for(v=vecs) R * v];


// tetrahedron();
// disdyakis_triacontahedron();
figs = get_standardized_vertex_figures(vertices, edges);

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
