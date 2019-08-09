"""
Structures holding the several instantiated objects from the configuration
"""
import numpy
import logging
from os import path as Path
from .core import NeurodamusCore as Nd


class ElectrodeManager(object):
    """ Electrode Manager.
        Create and handle electrodes according to configuration
    """
    __slots__ = ['_pos', '_names', '_electrodes', '_count']

    def __init__(self, elec_path, elecs_conf):
        """Init for ElectrodeManager.
        Args:
            elec_path: (string) The path where te find the electrodes config
            elecs_conf: A python Mapping of the configurations
        """
        self._names = []
        self._electrodes = []
        self._count = len(elecs_conf)
        self._pos = numpy.empty((self._count, 3), dtype='int32')  # x,y,z
        cur_i = 0

        for name, conf in elecs_conf.items():
            el_file = conf.get("File")
            if not el_file:
                logging.warning("No File speficied for electrode %s. Skipping", name)
                continue
            el_filepath = Path.join(elec_path, el_file.s)

            # Get electrode, checking versions
            v = conf.get("Version")  # Either None or hocObject
            if v is not None and v.s == "5":
                tmp_elec = Nd.lookupTableV2(el_filepath)
                v = tmp_elec.vInfo()
            if v != 5:
                logging.warning("Invalid Electrode version found. Only version 5 is supported")
                continue

            # Get & convert xyz - int() base 0 is autodetect (eq to %i)
            xyz = [int(conf.get(vname).s, 0) for vname in "xyz"]

            # Store info
            self._names.append(name)
            self._electrodes.append(tmp_elec)
            self._pos[cur_i] = xyz
            cur_i += 1

    def get(self, elec_id):
        """Retrieves an electrode object given its name or index.

        Raises: KeyError if the element doesnt exist
        """
        if isinstance(elec_id, str):
            for i, cur_name in enumerate(self._names):
                if cur_name == elec_id:
                    elec_id = i
                    break
            else:
                raise KeyError("ElectrodeManager> Non-existing name: %s" % elec_id)
        return self._electrodes[elec_id]

    def find_near(self, x, y, z):
        """Retrieves an electrode object given a <x, y, z> position.

        Returns: the first Electrode object found within 5 micron (in each direction),
            or None if not found
        """
        all_dist = numpy.absolute(self._pos - (x, y, z))
        for elec, dist in zip(self._electrodes, all_dist):
            if (dist < 5).all():
                return elec
        return None

    def get_name(self, i):
        return self._names[i]

    def get_position(self, i):
        return self._pos[i]

    def __len__(self):
        return self._count
