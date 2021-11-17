#!/bin/bash
#  - Blue Brain Project -
# This script builds the mod extensions to neurodamus. The folder gets named _lib

set -euxo pipefail

CORE_DIR="$1"

if [ -d _lib ]; then
    exit 0
fi

MOD_BUILD_DIR="mods.tmp"
mkdir -p $MOD_BUILD_DIR
cp -f $CORE_DIR/mod/*.mod $MOD_BUILD_DIR
cp -f $CORE_DIR/models/common/mod/*.mod $MOD_BUILD_DIR
nrnivmodl -incflags "-DDISABLE_REPORTINGLIB -DDISABLE_HDF5 -DDISABLE_MPI" $MOD_BUILD_DIR
if [ ! -f x86_64/special ]; then
    echo "Error running nrnivmodl"
    exit 1
fi
mkdir -p _lib
mv x86_64/libnrnmech* _lib/
cp -f $CORE_DIR/hoc/*.hoc _lib/
cp -f $CORE_DIR/models/common/hoc/*.hoc _lib/
