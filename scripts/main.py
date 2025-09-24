import os
import subprocess
from parser import Parser

path = "../scad"
url = "https://dmccooey.com/polyhedra/"
data_dir = "../data/"

def download_polyhedra():
    for directory in os.listdir(path):
        if os.path.isfile(os.path.join(path, directory)):
            continue
        data = directory.split("-")
        fname = data[2:]
        output_fname = ""
        for name in fname:
            output_fname += name[0].upper()
            output_fname += name[1:].lower()
        output_fname += ".txt"
        if os.path.isfile(os.path.join(data_dir, output_fname)):
            continue
        subprocess.call(
            ["wget", "-c", url + output_fname, "-O", data_dir + output_fname]
        )

def generate_vertices_scad():
    for directory in os.listdir(path):
        if os.path.isfile(os.path.join(path, directory)):
            continue
        data = directory.split("-")
        fname = data[2:]
        output_fname = ""
        for name in fname:
            output_fname += name[0].upper()
            output_fname += name[1:].lower()
        output_fname += ".txt"
        if not os.path.isfile(os.path.join(data_dir, output_fname)):
            continue
        with open(data_dir + output_fname) as f:
            try:
                parser = Parser(f.read())
                polyhedron = parser.polyhedron()
            except:
                continue
        with open(path + "/" + directory + "/geometry.scad", "w") as f:
            f.write(polyhedron.openscad())



if __name__ == "__main__":
    download_polyhedra()
    generate_vertices_scad()
