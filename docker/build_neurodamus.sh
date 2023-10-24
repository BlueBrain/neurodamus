#!/bin/bash

echo "build models from folder " $1
nrnivmodl -coreneuron -incflags '-DENABLE_CORENEURON -I${SONATAREPORT_DIR}/include -I/usr/include/hdf5/mpich -I/usr/lib/x86_64-linux-gnu/mpich' -loadflags '-L${SONATAREPORT_DIR}/lib -lsonatareport -Wl,-rpath,${SONATAREPORT_DIR}/lib -L/usr/lib/x86_64-linux-gnu/hdf5/mpich -lhdf5 -Wl,-rpath,/usr/lib/x86_64-linux-gnu/hdf5/mpich/ -L/usr/lib/x86_64-linux-gnu/ -lmpich -Wl,-rpath,/usr/lib/x86_64-linux-gnu/' "$1"
