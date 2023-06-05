"""
Test suite for Neurodamus NGV support
"""
import os
import subprocess
from pathlib import Path

import libsonata
import numpy as np
import pytest

from neurodamus import Neurodamus
from neurodamus.ngv import GlioVascularManager

SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "ngv"
BLUECONFIG_FILE = SIM_DIR / "BlueConfig"

pytestmark = [
    pytest.mark.forked,
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
        reason="Test requires loading a neocortex model to run",
    ),
]


def load_neurodamus_neocortex_multiscale():
    module_output = subprocess.run(
        ["module load unstable; module show neurodamus-neocortex-multiscale"],
        capture_output=True,
        text=True,
        shell=True,
    )
    nrn_mech_path = None
    ld_library_path = None
    for line in module_output.stderr.split("\n"):
        if "NRNMECH_LIB_PATH" in line:
            nrn_mech_path = line.split(" ")[2]
            ld_library_path = os.path.dirname(nrn_mech_path)
    if nrn_mech_path is not None:
        os.environ["NRNMECH_LIB_PATH"] = nrn_mech_path
        os.environ["LD_LIBRARY_PATH"] = (
            ld_library_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")
        )
    else:
        module_output = subprocess.run(
            ["module load unstable; module show neurodamus-neocortex"],
            capture_output=True,
            text=True,
            shell=True,
        )
        raise Exception(
            "Right module not found. Output of 'module av neurodamus-neocortex': {}\n"
            "MODULEPATH: {}".format(module_output.stderr, os.environ.get("MODULEPATH"))
        )


def get_manager(ndamus):
    return ndamus.circuits.get_edge_manager(
        "vasculature", "astrocytes", GlioVascularManager
    )


def get_R0pas(astro_id, manager):
    astrocyte = manager._cell_manager.gid2cell[astro_id + manager._gid_offset]
    if astrocyte.endfeet is None:
        return []
    return [sec(0.5).vascouplingB.R0pas for sec in astrocyte.endfeet]


def get_Rad(astro_id, manager):
    astrocyte = manager._cell_manager.gid2cell[astro_id + manager._gid_offset]
    if astrocyte.endfeet is None:
        return []
    return [sec(0.5).vascouplingB.Rad for sec in astrocyte.endfeet]


def get_R0pas_ref(astro_id, manager):
    """
    Get R0pas using libsonata, without ndamus

    We need manager just for the paths (they could also be hardcoded)
    """

    path = manager.circuit_conf["Path"]
    storage = libsonata.EdgeStorage(path)
    pop_name = list(storage.population_names)[0]
    gliovascular_pop = storage.open_population(pop_name)

    path = manager.circuit_conf["VasculaturePath"]
    storage = libsonata.NodeStorage(path)
    pop_name = list(storage.population_names)[0]
    vasculature_pop = storage.open_population(pop_name)

    endfeet = gliovascular_pop.afferent_edges(astro_id)
    vasc_node_ids = libsonata.Selection(gliovascular_pop.source_nodes(endfeet))

    d_vessel_starts = vasculature_pop.get_attribute("start_diameter", vasc_node_ids)
    d_vessel_ends = vasculature_pop.get_attribute("end_diameter", vasc_node_ids)

    return [
        (d_vessel_start + d_vessel_end) / 4
        for d_vessel_start, d_vessel_end in zip(d_vessel_starts, d_vessel_ends)
    ]


@pytest.mark.skip(
    reason="Seg fault with neurodamus-neocortex-1.12-2.15.0, see BBPBGLIB-1039")
def test_vasccouplingB_radii():
    load_neurodamus_neocortex_multiscale()
    ndamus = Neurodamus(
        str(BLUECONFIG_FILE),
        enable_reports=False,
        logging_level=None,
        enable_coord_mapping=True,
    )

    manager = get_manager(ndamus)
    astro_ids = manager._astro_ids

    R0pas = [r for astro_id in astro_ids for r in get_R0pas(astro_id, manager)]
    R0pas_ref = [r for astro_id in astro_ids for r in get_R0pas_ref(astro_id, manager)]

    assert np.allclose(R0pas, R0pas_ref)

    Rad = [r for astro_id in astro_ids for r in get_Rad(astro_id, manager)]
    base_rad_in_vasccouplingBmod = 14.7
    assert np.allclose(Rad, [base_rad_in_vasccouplingBmod] * len(Rad))

    ndamus.sim_init()

    R0pas_old = [r for astro_id in astro_ids for r in get_R0pas(astro_id, manager)]
    assert np.allclose(R0pas_old, R0pas_ref)
    Rad_old = [r for astro_id in astro_ids for r in get_Rad(astro_id, manager)]
    assert np.allclose(Rad_old, [base_rad_in_vasccouplingBmod] * len(Rad))

    ndamus.solve(2)

    R0pas_new = [r for astro_id in astro_ids for r in get_R0pas(astro_id, manager)]
    assert np.allclose(R0pas_new, R0pas_ref)
    Rad_new = np.array(
        [r for astro_id in astro_ids for r in get_Rad(astro_id, manager)]
    )
    assert np.all([i != base_rad_in_vasccouplingBmod for i in Rad_new])
    assert np.all((Rad_new < 15) & (Rad_new > 14))


if __name__ == "__main__":
    test_vasccouplingB_radii()
