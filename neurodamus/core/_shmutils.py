import os
import psutil

class SHMUtil:
    """Helper class for the SHM file transfer mechanism of CoreNEURON.
    """
    @staticmethod
    def get_rss():
        vm = psutil.virtual_memory()
        return (vm.total - vm.available)

    @staticmethod
    def get_shm_avail():
        return psutil.disk_usage("/dev/shm").free

    @staticmethod
    def get_datadir_shm(datadir):
        shmdir = os.environ.get("SHMDIR")
        return None if not shmdir or not shmdir.startswith("/dev/shm/") \
                    else os.path.join(shmdir, os.path.abspath(datadir)[1:])

    @staticmethod
    def get_shm_factor():
        factor = os.environ.get("NEURODAMUS_SHM_FACTOR")
        return 0.4 if not factor or not 0.0 <= float(factor) <= 1.0 \
                   else float(factor)
