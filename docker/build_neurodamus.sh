#!/bin/bash

echo "build models from folder " $1

NRNIVMODL_INCLUDE_FLAGS="-I${SONATAREPORT_DIR}/include -I/usr/include/hdf5/mpich -I/usr/lib/x86_64-linux-gnu/mpich"
NRNIVMODL_LOAD_FLAGS="-L${SONATAREPORT_DIR}/lib -lsonatareport -Wl,-rpath,${SONATAREPORT_DIR}/lib -L/usr/lib/x86_64-linux-gnu/hdf5/mpich -lhdf5 -Wl,-rpath,/usr/lib/x86_64-linux-gnu/hdf5/mpich/ -L/usr/lib/x86_64-linux-gnu/ -lmpich -Wl,-rpath,/usr/lib/x86_64-linux-gnu/"

if [[ "$2" == "--only-neuron" ]]; then
    nrnivmodl -incflags ${NRNIVMODL_INCLUDE_FLAGS} -loadflags ${NRNIVMODL_LOAD_FLAGS} "$1"
else
    nrnivmodl -coreneuron -incflags "-DENABLE_CORENEURON ${NRNIVMODL_INCLUDE_FLAGS}" -loadflags "${NRNIVMODL_LOAD_FLAGS}" "$1"
fi
