#!/usr/bin/env freecadcmd

import os
import sys

import Draft
import Mesh
import Part

import FreeCAD as App

args = sys.argv[3:]

if len(args) < 2:
    print("Usage: step_to_stl.py input_file.step [output_file.stl] [scale_factor]")
    sys.exit(1)

infile = args[1]
if len(args) >= 3:
    outfile = args[2]
else:
    base, _ = os.path.splitext(infile)
    outfile = base + ".stl"

# Optional scale factor (default 0.001)
scale_factor = 0.001
if len(args) >= 4:
    scale_factor = float(args[3])

print(f"Converting {infile} -> {outfile} (scale: {scale_factor})")

# Load STEP file
shape = Part.Shape()
shape.read(infile)

# Create new doc
doc = App.newDocument()

# Add shape to document
pf = doc.addObject("Part::Feature", "myShape")
pf.Shape = shape

# Create scaled clone
clone = Draft.make_clone(pf)
clone.Scale = App.Vector(scale_factor, scale_factor, scale_factor)
doc.recompute()

# Export the clone to STL
Mesh.export([clone], outfile)

print("Finished export.")
