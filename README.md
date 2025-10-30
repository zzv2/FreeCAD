# FreeCAD

## Install

```bash
sudo snap install freecad
```

## Usage

### STL to STEP (batch)

```bash
bash src/batch_stl_to_step.sh ~/Documents/CAD/STL_to_STEP
```

This will convert all STL files in the specified directory to STEP format using FreeCAD.

### STEP to STL (batch)

```bash
bash src/batch_step_to_stl.sh ~/Documents/CAD/STEP_to_STL
```

This will convert all STEP files in the specified directory to STL format using FreeCAD.

You can also specify a custom scale factor (default is 0.001):

```bash
bash src/batch_step_to_stl.sh ~/Documents/CAD/STEP_to_STL 0.002
```
