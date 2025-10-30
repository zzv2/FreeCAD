#!/bin/bash
# batch_step_to_stl.sh
# Usage: batch_step_to_stl.sh /path/to/directory [scale_factor]

DIR=$1
SCALE_FACTOR=${2:-0.001}

if [ -z "${DIR}" ]; then
	echo "Usage: $0 directory_of_step_files [scale_factor]"
	echo "  scale_factor defaults to 0.001 if not provided"
	exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find "${DIR}" -type f \( -iname "*.step" -o -iname "*.stp" \) | while read -r STEPFILE; do
	STLFILE="${STEPFILE%.*}.stl"
	echo "################ Converting: ${STEPFILE} -> ${STLFILE} (scale: ${SCALE_FACTOR}) ################"
	# call FreeCAD script
	freecad.cmd --console "$(cat ${SCRIPT_DIR}/step_to_stl.py)" --pass "${STEPFILE}" "${STLFILE}" "${SCALE_FACTOR}"
done
