#!/usr/bin/env bash
set -xe

SIMDIR=$1
CONFIG_FILE=${2:-BlueConfig}
mpi_launcher=${3}
#srun --pty python -m pdb $NEURODAMUS_PYTHON/init.py --configFile=${SIMDIR}/BlueConfig --verbose

$mpi_launcher neurodamus ${SIMDIR}/${CONFIG_FILE} --verbose

if [ -d "${SIMDIR}/results/" ]; then
  sort -n -k1,1 -k2 < output/out.dat > output/out.sorted
  diff output/out.sorted ${SIMDIR}/results/out.sorted
  cmp output/soma.bbp ${SIMDIR}/results/soma.bbp
  cmp output/compartments.bbp ${SIMDIR}/results/compartments.bbp
fi
