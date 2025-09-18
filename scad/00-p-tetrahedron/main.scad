use <../constants.scad>

basic_coordinates = [
    [1, 1, 1],
    [-1, 1, -1],
    [-1, -1, 1],
    [1, -1, -1],
];

edges = [
    [0, 1],
    [0, 2],
    [0, 3],
    [1, 2],
    [1, 3],
    [2, 3],
];

edge_scale = 2 * sqrt(2);
midsphere_radius = edge_scale / sqrt(8);
coordinates = basic_coordinates / midsphere_radius;

module tetrahedron() {
    hedron(coordinates, edges);
}
