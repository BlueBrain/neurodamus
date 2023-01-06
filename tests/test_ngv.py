"""
Test suite for Neurodamus NGV support
"""
import os
import pytest
import subprocess
from pathlib import Path

from neurodamus import Neurodamus
from neurodamus.ngv import GlioVascularManager

SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "ngv"
BLUECONFIG_FILE = SIM_DIR / "BlueConfig"

pytestmark = [
    pytest.mark.forked,
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
        reason="Test requires loading a neocortex model to run"
    )
]

@pytest.fixture(scope="module")
def _setup():
    module_output = subprocess.run(['module show neurodamus-neocortex-multiscale'], capture_output=True, text=True, shell=True)
    nrn_mech_path = None
    ld_library_path = None
    for line in module_output.stderr.split("\n"):
        if "NRNMECH_LIB_PATH" in line:
            nrn_mech_path = line.split(" ")[2]
            ld_library_path = '/'.join(nrn_mech_path.split("/")[0:-1])
    if nrn_mech_path is not None:
        os.environ["NRNMECH_LIB_PATH"] = nrn_mech_path
        os.environ["LD_LIBRARY_PATH"] = ld_library_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")
    yield

def get_manager(ndamus):
    return ndamus.circuits.get_edge_manager(
                "vasculature", "astrocytes", GlioVascularManager
            )

def get_radii(astro_id, manager):
    astrocyte = manager._cell_manager.gid2cell[astro_id + manager._gid_offset]
    if astrocyte.endfeet is None:
        return []
    return [sec(0.5).vascouplingB.Rad for sec in astrocyte.endfeet]

def test_vasccouplingB_radii(_setup):
    ndamus = Neurodamus(
        str(BLUECONFIG_FILE),
        enable_reports=False,
        logging_level=None,
        enable_coord_mapping=True,
    )

    manager = get_manager(ndamus)
    astro_ids = manager._astro_ids
    radii = [r for astro_id in astro_ids for r in get_radii(astro_id, manager)]
    # I am not sure, I would need to check the results. I think the following check is correct
    assert all(i != 20 for i in radii)

    ndamus.sim_init()

    radii_old = [r for astro_id in astro_ids for r in get_radii(astro_id, manager)]
    assert all(i != 20 for i in radii)


    ndamus.solve(2)

    radii_new = [r for astro_id in astro_ids for r in get_radii(astro_id, manager)]
    assert any(i != j for i, j in zip(radii_old, radii_new))


if __name__ == "__main__":
    test_vasccouplingB_radii()
