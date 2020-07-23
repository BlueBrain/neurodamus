from neurodamus.io.config_parser import BlueConfig, BlueConfigParserError
from os import path as ospath
import pytest
from contextlib import contextmanager

BLUECONFIG_FILE = ospath.abspath(ospath.join(
    ospath.dirname(__file__), "simulations", "complex.blueconfig"))


def test_blueconfig_parser():
    bc = BlueConfig(BLUECONFIG_FILE)
    assert bc.Run['BaseSeed'] == 10
    assert bc.Run['RNGMode'] == "UpdatedMCell"
    assert bc.Report['soma']['Dt'] == 0.5
    assert 100.457 < bc.Stimulus['ThresholdInh']['MeanPercent'] < 100.458


@contextmanager
def patch_line(nr, new_line):
    original_f = BlueConfig._parse_top

    def parse_top_patch(self, f):
        f = list(f)
        f[nr] = new_line
        original_f(self, iter(f))

    BlueConfig._parse_top = parse_top_patch
    yield
    BlueConfig._parse_top = original_f


def test_blueconfig_err_no_close():
    with patch_line(32, "# } was here"):
        with pytest.raises(BlueConfigParserError,
                           match="'Run Default': Section not closed"):
            BlueConfig(BLUECONFIG_FILE)


def test_blueconfig_commented_section():
    with patch_line(40, "# Report soma"):
        bc = BlueConfig(BLUECONFIG_FILE)
        assert "soma" not in bc.Report


def test_blueconfig_err_single_token():
    with patch_line(20, "missing_value"):
        with pytest.raises(BlueConfigParserError,
                           match="Invalid data in section 'Run Default': missing_value"):
            BlueConfig(BLUECONFIG_FILE)


def test_require_run():
    with patch_line(0, "# Run section commented"):
        with pytest.raises(BlueConfigParserError, match="Section 'Run' doesn't exist"):
            BlueConfig(BLUECONFIG_FILE)


if __name__ == "__main__":
    test_blueconfig_parser()
    test_blueconfig_err_no_close()
    test_blueconfig_commented_section()
    test_blueconfig_err_single_token()
    test_require_run()
