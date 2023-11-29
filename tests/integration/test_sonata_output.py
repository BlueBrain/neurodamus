import os
import json
import pytest
from tempfile import NamedTemporaryFile

pytestmark = pytest.mark.forked  # independent processes


def test_sonata_logfile(sonata_config):
    from neurodamus.node import Node
    sonata_config["output"] = {"log_file": "my_pydamus.log"}
    # create a tmp json file to test the user defined log_file
    with NamedTemporaryFile("w", suffix=".json", delete=False) as config_file:
        json.dump(sonata_config, config_file)
    _ = Node(config_file.name)

    assert os.path.exists("my_pydamus.log")
    os.unlink(config_file.name)


def test_throw_spike_sort_order(sonata_config):
    from neurodamus.node import Node
    from neurodamus.core.configuration import ConfigurationError

    sonata_config["output"] = {"spikes_sort_order": "by_id"}
    # create a tmp json file to throw with the wrong spike_sort_order
    with NamedTemporaryFile("w", suffix=".json", delete=False) as config_file:
        json.dump(sonata_config, config_file)
    with pytest.raises(ConfigurationError, match=r"Unsupported spikes sort order by_id"):
        _ = Node(config_file.name)

    os.unlink(config_file.name)
