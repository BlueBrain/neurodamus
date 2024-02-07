import os
import pytest

assert os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"), \
    "Test requires loading a neocortex model to run"

pytestmark = [
    pytest.mark.forked,
]
