# Vertexprint

Vertexprint is a tool for converting meshes into 3D printable assemblies.
The tool takes a mesh as input and generates:

- **STL files for vertex holders** - printed components that hold rods in place.
- **A table of edge lengths** - cut your rods to these lengths, either by hand or with a laser cutter.

The generated assemblies use interference fits: vertex holders have slots that
rods slide into. For complex parts, vertex pieces and edges can be labeled.
Each slot on each vertex is labeled with the corresponding edge; use these slot
numbers to determine which edges go where.

If you use a laser cutter to cut your rods, then vertexprint also generates SVG
files to cut rods in batches.


## Usage
```bash
# View all options
uv run python scripts/parser.py --help

# Preview a cube
uv run python scripts/parser.py --file data/cube.txt

# Generate vertex pieces for a cube
uv run python scripts/parser.py --file data/cube.txt --generate-outputs


uv run python scripts/parser.py \
    --file data/Bunny-LowPoly.stl \
    --offset-type per_half_edge \       # Vertex pieces can have nonuniform offsets
    --radius 750 \                      # Rescale object such that the vertex furthest from the origin has this distance from the origin
    --rod-inset 6 \                     # Rods are inset by this distance
    --isotropize \                      # Make faces as equilateral as possible (avoids small angles)
    --label-vertices \                  # Add labels to vertex pieces
    --generate-outputs
```

## Installation & Development

This project uses Nix for environment management and `uv` for Python
dependencies. You only need to have Nix installed to develop for this project.
Nix manages everything else for you.

```bash
# Enter the development shell
nix develop

# Install dependencies with uv
uv sync

# Run tests
uv run pytest
```
