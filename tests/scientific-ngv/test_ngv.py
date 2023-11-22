"""
Test suite for Neurodamus NGV support
"""
from pathlib import Path

import libsonata
import numpy as np

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "ngv"
SONATACONFIG_FILE = SIM_DIR / "simulation_config.json"


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

    manager.open_edge_location(manager.circuit_conf["Path"], manager.circuit_conf)
    gliovascular_pop = manager._gliovascular
    vasculature_pop = manager._vasculature
    endfeet = gliovascular_pop.afferent_edges(astro_id)
    vasc_node_ids = libsonata.Selection(gliovascular_pop.source_nodes(endfeet))

    d_vessel_starts = vasculature_pop.get_attribute("start_diameter", vasc_node_ids)
    d_vessel_ends = vasculature_pop.get_attribute("end_diameter", vasc_node_ids)

    return [
        (d_vessel_start + d_vessel_end) / 4
        for d_vessel_start, d_vessel_end in zip(d_vessel_starts, d_vessel_ends)
    ]


def test_vasccouplingB_radii():
    from neurodamus import Neurodamus
    from neurodamus.ngv import GlioVascularManager
    ndamus = Neurodamus(
        str(SONATACONFIG_FILE),
        enable_reports=False,
        logging_level=None,
        enable_coord_mapping=True,
    )

    manager = ndamus.circuits.get_edge_manager("vasculature", "astrocytes", GlioVascularManager)
    astro_ids = manager._astro_ids

    R0pas = [r for astro_id in astro_ids for r in get_R0pas(astro_id, manager)]
    R0pas_ref = [r for astro_id in astro_ids for r in get_R0pas_ref(astro_id-1, manager)]

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
