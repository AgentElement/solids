phi = 10;
r = 10;
l = 50;
theta = 60;
h = 10;

rotate([0, 90-phi, 0])
cylinder(h=l);

// rotate([0, 90, 0])

translate([50 * sin(90-phi), 0, 50 * cos(90-phi)])
rotate([0, 180-phi, 0])
cylinder(h=r);


function length(r, l, theta, phi, h) =
    r > l * tan(phi) ? l * sin(theta) :
        (l * sin(theta-phi) + r * cos(theta-phi)) / sin(theta) - h * (1/tan(phi) - 1/tan(theta));

function height(r, l, theta, phi, h) =
    r > l * tan(phi) ? 0 : h;

length = length(r, l, theta, phi, h);
height = height(r, l, theta, phi, h);

translate([h / tan(phi), 0, height])
rotate([0, 90, 0])
cylinder(h=length);

translate([h / tan(phi) + length, 0, height])
rotate([0, 90-theta, 0])
cylinder(h=20);
