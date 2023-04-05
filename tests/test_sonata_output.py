import os
import json
import pytest
from tempfile import NamedTemporaryFile
from neurodamus.node import Node

pytestmark = pytest.mark.forked  # independent processes


# Currently exclude this test from base tests because of failure,
# perhaps NEURON and log file has been initialised by some unforked test.
# TODO: Review our unit tests with marker pytest.mark.slow
# so as to exclude them from base tests by pytest -m "not slow"
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_sonata_logfile(sonata_config):
    sonata_config["output"] = {"log_file": "my_pydamus.log"}
    # create a tmp json file to test the user defined log_file
    with NamedTemporaryFile("w", suffix=".json", delete=False) as config_file:
        json.dump(sonata_config, config_file)
    _ = Node(config_file.name)

    assert os.path.exists("my_pydamus.log")
    os.unlink(config_file.name)


def test_throw_spike_sort_order(sonata_config):
    from neurodamus.core.configuration import ConfigurationError

    sonata_config["output"] = {"spikes_sort_order": "by_id"}
    # create a tmp json file to throw with the wrong spike_sort_order
    with NamedTemporaryFile("w", suffix=".json", delete=False) as config_file:
        json.dump(sonata_config, config_file)
    with pytest.raises(ConfigurationError, match=r"Unsupported spikes sort order by_id"):
        _ = Node(config_file.name)

    os.unlink(config_file.name)
