EDGE_D = 5;
UNIT = 60;

// Create a cylinder between two points 'a' and 'b' with radius 'r'.
// Optionally, offset cylinder inward by 'o'.
module edge(a, b, d, o=0) {
    v = b - a;
    dist = norm(v);
    u = v / dist;
    a_new = a + u * o;
    h = dist - 2 * o;

    translate(a_new)
    rotate([0, acos(v.z/h), atan2(v.y, v.x)])
    cylinder(h = h, d = d, $fn = 32);
}

module hedron(coordinates, edges) {
    for (edge = edges) {
        a = coordinates[edge[0]] * UNIT;
        b = coordinates[edge[1]] * UNIT;
        edge(a, b, EDGE_D);
    }
}

module unit_sphere() {
    sphere(r=UNIT);
}
