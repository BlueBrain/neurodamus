#!/usr/bin/env bash
set -xe

SIMDIR=$1

mpiexec neurodamus ${SIMDIR}/BlueConfig --verbose

sort -n -k1,1 -k2 < output/out.dat > output/out.sorted
diff output/out.sorted ${SIMDIR}/results/out.sorted
cmp output/soma.bbp ${SIMDIR}/results/soma.bbp
cmp output/compartments.bbp ${SIMDIR}/results/compartments.bbp
