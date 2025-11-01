import sys

import importDXF  # FreeCAD's DXF importer module
import Part

import FreeCAD as App

args = sys.argv[3:]

if len(args) < 3:
    print("Usage: dxf2step.py input_file.dxf output_file.step [extrude_height]")
    sys.exit(1)

infile = args[1]
outfile = args[2]
extrude_height = float(args[3]) if len(args) >= 4 else 1.0  # default 1 unit

print(f"infile: {infile}")
print(f"outfile: {outfile}")
print(f"extrude_height: {extrude_height}")
print(f"Importing DXF: {infile}")
doc = App.newDocument("DXFtoSTEP")

# Import the DXF file
importDXF.insert(infile, doc.Name)

doc.recompute()

# Assume the imported objects are Draft/Sketch wires or shapes
# Find all wire shapes, then extrude them
solids = []
for obj in doc.Objects:
    if hasattr(obj, "Shape"):
        shp = obj.Shape
        # Choose only wires or faces to extrude
        if shp.Faces:
            # extrude faces into a solid
            solid = Part.makePrism(shp, App.Vector(0, 0, extrude_height))
            partobj = doc.addObject("Part::Feature", f"SolidFrom_{obj.Name}")
            partobj.Shape = solid
            solids.append(partobj)

doc.recompute()

if not solids:
    print("Warning: No faces found to extrude. Please check DXF content.")
else:
    # If multiple solids, you may fuse them
    if len(solids) > 1:
        fused = Part.makeCompound([o.Shape for o in solids])
        fused_obj = doc.addObject("Part::Feature", "FusedSolids")
        fused_obj.Shape = fused
        export_obj = fused_obj
    else:
        export_obj = solids[0]

print(f"Exporting STEP: {outfile}")
export_obj.Shape.exportStep(outfile)
print("Done.")
