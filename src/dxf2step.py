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

# Collect all edges from imported objects
all_edges = []
for obj in doc.Objects:
    if hasattr(obj, "Shape") and obj.Shape.Edges:
        all_edges.extend(obj.Shape.Edges)

print(f"Collected {len(all_edges)} edges from DXF")

# Try to create wires from the edges
try:
    print("Attempting to connect edges into wires...")
    wires = Part.sortEdges(all_edges)
    print(f"Created {len(wires)} wire groups")
except Exception as e:
    print(f"Error sorting edges: {e}")
    wires = []

# Create solids from wires
solids = []
for i, edge_list in enumerate(wires):
    try:
        # Create a wire from the edge list
        wire = Part.Wire(edge_list)
        print(f"Wire {i}: closed={wire.isClosed()}, {len(edge_list)} edges")

        if wire.isClosed():
            # Create face and extrude
            face = Part.Face(wire)
            solid = face.extrude(App.Vector(0, 0, extrude_height))
            partobj = doc.addObject("Part::Feature", f"Solid_{i}")
            partobj.Shape = solid
            solids.append(partobj)
            print(f"  Created solid from wire {i}")
        else:
            print(f"  Wire {i} is not closed, skipping")
    except Exception as e:
        print(f"  Failed to create solid from wire {i}: {e}")

doc.recompute()

if not solids:
    print("Warning: No faces found to extrude. Please check DXF content.")
    sys.exit(1)
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
