import os
import subprocess
from parser import Parser

scad_dir = "../scad"
url = "https://dmccooey.com/polyhedra/"
data_dir = "../data/"
polyhedron_file = "polyhedron_list.txt"


def make_filename(polyhedron: str) -> str:
    data = polyhedron.split("-")[2:]
    filename = ""
    for name in data:
        filename += name[0].upper()
        filename += name[1:].lower()
    filename += ".txt"
    return filename


def download_polyhedra():
    with open(data_dir + polyhedron_file) as file:
        polyhedron_list = file.read().splitlines()
    for polyhedron in polyhedron_list:
        filename = make_filename(polyhedron)
        filepath = os.path.join(data_dir, filename)
        if os.path.isfile(filepath):
            continue
        subprocess.call(["wget", "-c", url + filename, "-O", filepath])
        try:
            with open(filepath, "r", encoding="ascii") as file:
                file.read()
        except UnicodeDecodeError:
            print(f"Cannot download {polyhedron}")
            os.remove(filepath)


def generate_vertices_scad():
    scad_geometry = "include <geometry_utils.scad>\n"
    with open(data_dir + polyhedron_file) as file:
        polyhedron_list = file.read().splitlines()
    for polyhedron in polyhedron_list:
        filename = make_filename(polyhedron)
        filepath = os.path.join(data_dir, filename)
        if not os.path.isfile(filepath):
            continue
        with open(filepath) as file:
            try:
                parser = Parser(file.read())
                polyhedron = parser.polyhedron()
            except Exception as e:
                print(f"{filename}: {e}")
                continue
        scad_geometry += polyhedron.openscad() + "\n"
    with open(os.path.join(scad_dir, "geometry.scad"), "w") as f:
        f.write(scad_geometry)


if __name__ == "__main__":
    download_polyhedra()
    generate_vertices_scad()
