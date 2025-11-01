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

# Scale factor: DXF units are in cm, scale to meters
scale_factor = 0.01

# Collect all edges from imported objects and scale them
all_edges = []
for obj in doc.Objects:
    if hasattr(obj, "Shape") and obj.Shape.Edges:
        for edge in obj.Shape.Edges:
            # Scale the edge geometry
            scaled_edge = edge.scaled(scale_factor)
            all_edges.append(scaled_edge)

print(f"Collected {len(all_edges)} edges from DXF (scaled to meters)")

# Try to create wires from the edges
try:
    print("Attempting to connect edges into wires...")
    wires = Part.sortEdges(all_edges)
    print(f"Created {len(wires)} wire groups")
except Exception as e:
    print(f"Error sorting edges: {e}")
    wires = []

# Create solids from wires
faces_and_wires = []
for i, edge_list in enumerate(wires):
    try:
        # Create a wire from the edge list
        wire = Part.Wire(edge_list)
        print(f"Wire {i}: closed={wire.isClosed()}, {len(edge_list)} edges")

        if wire.isClosed():
            # Create face
            face = Part.Face(wire)
            faces_and_wires.append((i, face, wire))
            print(f"  Created face from wire {i}")
        else:
            print(f"  Wire {i} is not closed, skipping")
    except Exception as e:
        print(f"  Failed to create face from wire {i}: {e}")

# Determine which faces are inside other faces
print("\nAnalyzing face containment...")
face_levels = {}  # Maps face index to containment level (0 = outermost)

for i, face_i, wire_i in faces_and_wires:
    contained_by = []
    for j, face_j, wire_j in faces_and_wires:
        if i != j:
            # Check if face_i is inside face_j by testing if a point on wire_i
            # is inside face_j
            try:
                # Get a point on the wire
                test_point = wire_i.Vertexes[0].Point
                # Check if it's inside the other face
                if face_j.isInside(test_point, 0.001, True):
                    contained_by.append(j)
            except Exception:
                pass

    # Level is the number of faces containing this face
    face_levels[i] = len(contained_by)
    if contained_by:
        print(f"  Face {i} is inside faces: {contained_by}")

# Create solids with different heights based on containment level
solids = []
for i, face, wire in faces_and_wires:
    level = face_levels.get(i, 0)
    # Alternate heights: even levels use base height, odd levels use taller height
    if level % 2 == 0:
        height = extrude_height
    else:
        height = extrude_height * 1.5

    try:
        solid = face.extrude(App.Vector(0, 0, height))
        partobj = doc.addObject("Part::Feature", f"Solid_{i}_L{level}")
        partobj.Shape = solid
        solids.append(partobj)
        print(f"  Created solid from face {i} (level {level}, height {height})")
    except Exception as e:
        print(f"  Failed to create solid from face {i}: {e}")

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
