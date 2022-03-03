#!/bin/bash
#SBATCH --account=proj45
#SBATCH -C cpu
#SBATCH --nodes=1
#SBATCH --partition=prod
set -euo pipefail
unset $(set +x; env | awk -F= '/^(PMI|SLURM)_/ {print $1}' | xargs)
TESTNAME=${1:-tests/test_sonata_config.py}

export MODULEPATH=
source /gpfs/bbp.cscs.ch/apps/hpc/jenkins/config/modules.sh
module load unstable
module load neurodamus-neocortex  # will bring neuron and python
export PYTHONPATH="/gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/libraries/2021-01-06/linux-rhel7-x86_64/gcc-9.3.0/py-scipy-1.5.4-t6m7lq/lib/python3.8/site-packages:/gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/applications/2021-01-06/linux-rhel7-x86_64/gcc-9.3.0/py-libsonata-0.1.9.20210901-ebxuqv/lib/python3.8/site-packages:/gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/libraries/2021-01-06/linux-rhel7-x86_64/gcc-9.3.0/py-h5py-3.1.0-hsdjwk/lib/python3.8/site-packages:/gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/libraries/2021-01-06/linux-rhel7-x86_64/gcc-9.3.0/py-morphio-3.1.1-56sgab/lib/python3.8/site-packages:$PYTHONPATH"

if [ ! -d venv ]; then
    python -m venv venv
    source venv/bin/activate
    pip install -U pip setuptools
    pip install -e .
else
    source venv/bin/activate
fi

python $TESTNAME
