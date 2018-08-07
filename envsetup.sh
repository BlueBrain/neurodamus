. ~/.bashrc

module purge
module load nix/gcc nix/mvapich2 nix/phdf5 nix/hpc/reportinglib
. venv/bin/activate

#module load nix/py27/ipython

ND_BASE=$HOME/dev/neurodamus
export PATH=$PATH:$ND_BASE/result/bin
export HOC_LIBRARY_PATH="$ND_BASE/lib/hoclib"
export PYINIT="$ND_BASE/python/init.py"

