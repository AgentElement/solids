use <../constants.scad>

basic_coordinates = [
    [1, 1, 1],
    [1, 1, -1],
    [1, -1, 1],
    [1, -1, -1],
    [-1, 1, 1],
    [-1, 1, -1],
    [-1, -1, 1],
    [-1, -1, -1],
];

edges = [
    [0, 1],
    [0, 2],
    [0, 4],
    [7, ]
]


edge_scale = 2;
midsphere_radius = edge_scale / sqrt(2)
coordinates = basic_coordinates / midsphere_radius;

module cube() {
    hedron(coordinates, edges);
}
