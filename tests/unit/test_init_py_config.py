import pytest

import init

_default_config_file = 'simulation_config.json'


def test_init_empty():
    args = init.extract_arguments(['some/dir/init.py'])
    assert len(args) == 1
    assert args[0] == _default_config_file


def test_init_non_positional():
    with pytest.raises(ValueError):
        init.extract_arguments(['init.py', 'simulation_config.json'])


def test_init_config_only():
    args = init.extract_arguments(['another/dir/init.py', '--configFile=conf/my_config.json'])
    assert len(args) == 1
    assert args[0] == 'conf/my_config.json'


def test_init_pass_options():
    args = init.extract_arguments(['another/dir/init.py', '--foo=bar', '--configFile=conf/my_config.json',
                                   '-v', '--baz=qux'])
    assert len(args) == 4
    assert args[0] == 'conf/my_config.json'
    assert args[1] == '--foo=bar'
    assert args[2] == '-v'
    assert args[3] == '--baz=qux'
