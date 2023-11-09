import json
import os
from pathlib import Path
import pytest
import shutil
import subprocess
import tempfile


SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "v5_sonata"
CONFIG_FILE_MINI = "simulation_config_mini.json"


@pytest.mark.slow
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_save_restore_cli():
    with open(SIM_DIR / CONFIG_FILE_MINI, "r") as f:
        sim_config_data = json.load(f)

    for simulator in ("NEURON", "CORENEURON"):
        test_folder = tempfile.TemporaryDirectory("cli-test-" + simulator)  # auto removed
        test_folder_path = Path(test_folder.name)
        # Copy non-modified files
        for f in ("node_sets.json", "circuit_config.json", "input.dat"):
            shutil.copy(SIM_DIR / f, test_folder_path)

        for action, tstop in (("save", 100), ("restore", 200)):
            sim_config_data["target_simulator"] = simulator
            sim_config_data["run"]["tstop"] = tstop
            sim_config_data["output"]["output_dir"] = str(test_folder_path / ("output-" + action))

            with open(test_folder_path / CONFIG_FILE_MINI, "w") as f:
                json.dump(sim_config_data, f, indent=2)

            # Checkpoints inside the output good tradition w CoreNeuron
            checkpoint_dir = test_folder_path / "output-save" / "checkpoint"

            command = ["neurodamus", test_folder_path / CONFIG_FILE_MINI,
                        "--" + action, checkpoint_dir]
            # Save-Restore raises exception when using NEURON
            if simulator == "NEURON":
                with pytest.raises(subprocess.CalledProcessError):
                    subprocess.run(command, check=True)
            else:
                subprocess.run(command, check=True)


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_cli_prcellgid():
    test_folder = tempfile.TemporaryDirectory("cli-test-prcellgid")  # auto removed
    test_folder_path = Path(test_folder.name)
    for f in ("node_sets.json", "circuit_config.json", "input.dat", "simulation_config_mini.json"):
        shutil.copy(SIM_DIR / f, test_folder_path)

    subprocess.run(
        ["neurodamus", CONFIG_FILE_MINI, "--dump-cell-state", "62797"],
        check=True,
        cwd=test_folder_path
    )
    assert (test_folder_path / "62798_py_Neuron_t0.0.nrndat").is_file()
    assert (test_folder_path / "62798_py_Neuron_t100.0.nrndat").is_file()
