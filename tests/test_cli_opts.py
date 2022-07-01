import json
import os
from pathlib import Path
import pytest
import shutil
import subprocess

SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "v5_sonata"


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_save_restore_cli():
    config_file = "simulation_config_mini.json"

    with open(SIM_DIR / config_file, "r") as f:
        sim_config_data = json.load(f)

    for simulator in ("NEURON", "CORENEURON"):
        test_folder = Path.cwd() / ("cli-test-" + simulator)
        test_folder.mkdir(exist_ok=True)
        # Copy non-modified files
        for f in ("node_sets.json", "circuit_config.json", "input.dat"):
            shutil.copy(SIM_DIR / f, test_folder)

        for action, tstop in (("save", 100), ("restore", 200)):
            sim_config_data["target_simulator"] = simulator
            sim_config_data["run"]["tstop"] = tstop
            sim_config_data["output"]["output_dir"] = str(test_folder / ("output-" + action))

            with open(test_folder / config_file, "w") as f:
                json.dump(sim_config_data, f, indent=2)

            # Checkpoints inside the output good tradition w CoreNeuron
            checkpoint_dir = test_folder / "output-save" / "checkpoint"

            subprocess.run(
                ["neurodamus", test_folder / config_file, "--" + action, checkpoint_dir],
                check=True
            )


if __name__ == "__main__":
    test_save_restore_cli()
