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
        is_closed = wire.isClosed()
        print(f"Wire {i}: closed={is_closed}, {len(edge_list)} edges")

        # If not closed, check if it's nearly closed and try to fix it
        if not is_closed:
            # Get the start and end points
            first_vertex = wire.Vertexes[0].Point
            last_vertex = wire.Vertexes[-1].Point
            gap_distance = first_vertex.distanceToPoint(last_vertex)
            print(f"  Wire {i} gap distance: {gap_distance} meters")

            # If the gap is small enough, try to close it
            if gap_distance < 0.01:  # 1cm tolerance
                print(f"  Attempting to close wire {i} by adding a closing edge...")
                try:
                    # Create a line segment to close the gap
                    closing_edge = Part.LineSegment(last_vertex, first_vertex).toShape()
                    closed_edges = edge_list + [closing_edge]
                    wire = Part.Wire(closed_edges)
                    is_closed = wire.isClosed()
                    print(f"  Wire {i} after fix: closed={is_closed}")
                except Exception as e:
                    print(f"  Failed to close wire {i}: {e}")

        if is_closed:
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
    # Calculate bounding box for all faces
    print("\nCalculating bounding box for base plate...")
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for i, face, wire in faces_and_wires:
        bbox = face.BoundBox
        min_x = min(min_x, bbox.XMin)
        min_y = min(min_y, bbox.YMin)
        max_x = max(max_x, bbox.XMax)
        max_y = max(max_y, bbox.YMax)

    # Add 5% padding
    width = max_x - min_x
    height = max_y - min_y
    padding_x = width * 0.05
    padding_y = height * 0.05

    min_x -= padding_x
    min_y -= padding_y
    max_x += padding_x
    max_y += padding_y

    print(f"  Bounds: X=[{min_x:.4f}, {max_x:.4f}], Y=[{min_y:.4f}, {max_y:.4f}]")
    print(f"  Dimensions: {max_x - min_x:.4f} x {max_y - min_y:.4f} meters")

    # Create base plate rectangle at half the height of level 0 faces
    base_height = extrude_height * 0.5
    print(f"  Creating base plate with height {base_height} meters...")

    # Create rectangle vertices
    v1 = App.Vector(min_x, min_y, 0)
    v2 = App.Vector(max_x, min_y, 0)
    v3 = App.Vector(max_x, max_y, 0)
    v4 = App.Vector(min_x, max_y, 0)

    # Create edges
    l1 = Part.LineSegment(v1, v2).toShape()
    l2 = Part.LineSegment(v2, v3).toShape()
    l3 = Part.LineSegment(v3, v4).toShape()
    l4 = Part.LineSegment(v4, v1).toShape()

    # Create wire and face
    base_wire = Part.Wire([l1, l2, l3, l4])
    base_face = Part.Face(base_wire)
    base_solid = base_face.extrude(App.Vector(0, 0, base_height))

    base_obj = doc.addObject("Part::Feature", "BasePlate")
    base_obj.Shape = base_solid
    solids.insert(0, base_obj)  # Add at the beginning
    print("  Created base plate")

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
