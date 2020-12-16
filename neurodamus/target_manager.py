import itertools
import logging
import os.path
from .core.configuration import GlobalConfig, find_input_file
from .core import MPI, NeurodamusCore as Nd


class TargetManager:
    def __init__(self, run_conf):
        self._run_conf = run_conf
        self.parser = Nd.TargetParser()
        self.hoc = None  # The hoc level target manager
        # self._targets_fq = {}

    def load_targets(self, circuit):
        """Provided that the circuit location is known and whether a user.target file has been
        specified, load any target files via a TargetParser.
        Note that these will be moved into a TargetManager after the cells have been distributed,
        instantiated, and potentially split.
        """
        run_conf = self._run_conf
        if MPI.rank == 0:
            self.parser.isVerbose = 1

        if circuit.CircuitPath:
            start_target_file = os.path.join(circuit.CircuitPath, "start.target")
            if not os.path.isfile(start_target_file):
                logging.warning("start.target not available! Check circuit.")
            else:
                self.parser.open(start_target_file)

        if "TargetFile" in run_conf:
            user_target = find_input_file(run_conf["TargetFile"])
            self.parser.open(user_target, True)

        if MPI.rank == 0:
            logging.info(" => Loaded %d targets", self.parser.targetList.count())
            if GlobalConfig.verbosity >= 3:
                self.parser.printCellCounts()

    def get_target(self, target_name):
        return self.parser.getTarget(target_name)

    def init_hoc_manager(self, cell_manager):
        # give a TargetManager the TargetParser's completed targetList
        self.hoc = Nd.TargetManager(self.parser.targetList, cell_manager)

    def generate_subtargets(self, target_name, n_parts):
        """To facilitate CoreNeuron data generation, we allow users to use ModelBuildingSteps to
        indicate that the CircuitTarget should be split among multiple, smaller targets that will
        be built step by step.

        Returns:
            list with generated targets, or empty if no splitting was done
        """
        if not n_parts or n_parts == 1:
            return False

        target = self.parser.getTarget(target_name)
        allgids = target.completegids()
        new_targets = []

        for cycle_i in range(n_parts):
            target = Nd.Target()
            target.name = "{}_{}".format(target_name, cycle_i)
            new_targets.append(target)
            self.parser.updateTargetList(target)

        target_looper = itertools.cycle(new_targets)
        for gid in allgids.x:
            target = next(target_looper)
            target.gidMembers.append(gid)

        return new_targets
