#!/usr/bin/env freecadcmd

import os
import sys

import Mesh
import Part

import FreeCAD as App

args = sys.argv[3:]

if len(args) < 2:
    print("Usage: stl_to_step.py input_file.stl [output_file.step]")
    sys.exit(1)

infile = args[1]
if len(args) >= 3:
    outfile = args[2]
else:
    base, _ = os.path.splitext(infile)
    outfile = base + ".step"

print(f"Converting {infile} -> {outfile}")

# Load mesh
mesh = Mesh.Mesh(infile)

# Create new doc
doc = App.newDocument()

# Convert mesh to shape (tolerance value may need adjusting)
shape = Part.Shape()
shape.makeShapeFromMesh(mesh.Topology, 0.1)

# Convert shape to solid
solid = Part.makeSolid(shape)

# Add object for solid (needed for export)
obj = doc.addObject("Part::Feature", "SolidFromMesh")
obj.Shape = solid
doc.recompute()

# Export to STEP
solid.exportStep(outfile)

print("Finished export.")
