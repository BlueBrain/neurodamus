"""
A module definiting and running a simple engine.
We define ACell cells and corresponding managers
"""

import logging
import numpy as np
import os
import pytest
import subprocess
from pathlib import Path

from neurodamus.cell_distributor import CellManagerBase
from neurodamus.connection import ConnectionBase
from neurodamus.connection_manager import ConnectionManagerBase
from neurodamus.core import EngineBase
from neurodamus.io.synapse_reader import SynapseParameters
from neurodamus.io.cell_readers import split_round_robin
from neurodamus.metype import BaseCell

#
# Launching of the engine as a test
#
SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


class ACellType(BaseCell):
    """A new testing cell type
    """

    class CellName(str):
        pass

    def __init__(self, gid, cell_info, circuit_conf):
        """Instantiate a new Cell from node info"""
        from neurodamus.core import NeurodamusCore as Nd  # dont load top-level because of pytest
        super().__init__(gid, cell_info, circuit_conf)
        self.gid = gid
        self.section = Nd.Section(name="soma", cell=self.CellName("a" + str(gid)))
        self.f0 = cell_info[0]
        self.f1 = cell_info[1]

    def connect2target(self, target_pp=None):
        from neurodamus.core import NeurodamusCore as Nd
        return Nd.NetCon(self.section(1)._ref_v, target_pp, sec=self.section)


class ACellManager(CellManagerBase):
    CellType = ACellType

    @staticmethod
    def _node_loader(circuit_conf, gidvec, stride=1, stride_offset=0, **_kw):
        logging.info(" * HELLO from loading ACELL info")
        total_cells = 50

        gidvec = split_round_robin(gidvec, stride, stride_offset, total_cells)
        local_cell_count = len(gidvec)
        if not len(gidvec):  # Not enough cells to give this rank a few
            return gidvec, {}, total_cells

        properties = [
            np.ones(local_cell_count, dtype='f4'),  # fake field 1
            np.arange(local_cell_count, dtype='f4')  # fake field 2
        ]
        cell_info = dict(zip(gidvec, np.stack(properties, axis=-1)))
        return gidvec, cell_info, total_cells


class ACellConnection(ConnectionBase):
    """
    ACellConnections: simple so we aggregate all sources
    """
    def __init__(self, _, tgid, src_pop_id=0, dst_pop_id=0, weight_factor=1, sgids=None, **kw):
        """Init Connection. sgid as indexer is not used and set to None"""
        super().__init__(None, tgid, src_pop_id, dst_pop_id, weight_factor)
        self._src_gids = sgids or np.array([], dtype="uint32")
        self._synapse_params = ASynParameters.empty

    # Public properties
    conn_count = property(lambda self: len(self._src_gids))

    def append_src_cells(self, sgids, syn_params):
        self._src_gids = np.concatenate((self._src_gids, sgids))
        self._synapse_params = np.concatenate((self._synapse_params, syn_params))

    def finalize(self, target_cell, *_):
        from neurodamus.core import NeurodamusCore as Nd
        syn = Nd.ExpSyn(target_cell.section(0.5))
        self._synapses = (syn,)
        self._netcons = []

        for sgid, syn_params in zip(self._src_gids, self._synapse_params):
            nc = Nd.pc.gid_connect(sgid, syn)
            nc.weight[0] = syn_params.conductance * self._conn_params.weight_factor
            nc.delay = syn_params.delay
            self._netcons.append(nc)
        return len(self._src_gids)


class ASynParameters(SynapseParameters):
    _synapse_fields = ["sgid", "delay", "conductance"]


class ACellSynReader(object):
    def get_synapse_parameters(self, tgid, _mod=None):
        # for testing, each cell connects to src gids tgid+1 and tgid+2
        params = ASynParameters.create_array(2)
        params.sgid = [tgid+1, tgid+2]
        params.delay = 0.1
        params.conductance = 1
        return params


class ACellSynapseManager(ConnectionManagerBase):
    conn_factory = ACellConnection

    def open_synapse_file(self, synapse_file, n_synapse_files=None, src_pop_id=0):
        logging.info("Opening Synapse file %s", synapse_file)
        self._synapse_reader = ACellSynReader()

    def _add_synapses(self, cur_conn, syns_params, syn_type_restrict=None, base_id=0):
        cur_conn.append_src_cells(syns_params.sgid, syns_params)

    def _finalize_conns(self, tgid, conns, *_, **_kw):
        target_cell = self._cell_manager.get_cell(tgid)
        conns[0].finalize(target_cell)
        return conns[0].conn_count


class ACellEngine(EngineBase):
    CellManagerCls = ACellManager
    InnerConnectivityCls = ACellSynapseManager


@pytest.mark.skip(
    reason="Cannot test with SONATA configs, no SONATA parameter for Engine")
def test_run_acell_circuit():
    simdir = SIM_DIR / "acell_engine"
    env = os.environ.copy()
    env['NEURODAMUS_PYTHON'] = "."
    env['PYTHONPATH'] += ":" + os.path.dirname(__file__)
    env['NEURODAMUS_PLUGIN'] = os.path.splitext(os.path.basename(__file__))[0]
    subprocess.run(
        ["bash", "tests/test_simulation.bash", str(simdir), "BlueConfig", ""],
        env=env,
        check=True,
    )
