phi = 20;
r = 10;
l = 50;
theta = 60;

rotate([0, 90-phi, 0])
cylinder(h=l);

// rotate([0, 90, 0])

translate([50 * sin(90-phi), 0, 50 * cos(90-phi)])
rotate([0, 180-phi, 0])
cylinder(h=r);


function test(r, l, theta, phi) =
    r > l * tan(phi) ? 0 :
        (l * sin(theta-phi) + r * cos(theta-phi)) / sin(theta);

test = test(r, l, theta, phi);
rotate([0, 90, 0])
cylinder(h=test);

translate([test, 0, 0])
rotate([0, 90-theta, 0])
cylinder(h=20);
