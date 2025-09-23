import os
import subprocess


def main():
    path = "../scad"
    url = "https://dmccooey.com/polyhedra/"
    output = "../data/"
    for dname in os.listdir(path):
        if os.path.isfile(os.path.join(path, dname)):
            continue
        data = dname.split("-")
        fname = data[2:]
        dname = ""
        for name in fname:
            dname += name[0].upper()
            dname += name[1:].lower()
        dname += ".txt"
        if os.path.isfile(os.path.join(output, dname)):
            continue
        subprocess.call(["wget", "-c", url + dname, "-O", output + dname])


if __name__ == "__main__":
    main()
