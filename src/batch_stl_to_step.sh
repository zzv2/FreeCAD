#!/bin/bash
# batch_stl_to_step.sh
# Usage: batch_stl_to_step.sh /path/to/directory

DIR=$1
if [ -z "${DIR}" ]; then
	echo "Usage: $0 directory_of_stl_files"
	exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find "${DIR}" -type f -iname "*.stl" | while read -r STLFILE; do
	STEPFILE="${STLFILE%.*}.step"
	echo "################ Converting: ${STLFILE} -> ${STEPFILE} ################"
	# call FreeCAD script
	freecad.cmd --console "$(cat ${SCRIPT_DIR}/stl_to_step.py)" --pass "${STLFILE}" "${STEPFILE}"
done
