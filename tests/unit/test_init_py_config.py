import pytest

from neurodamus.utils.cli import extract_arguments

_default_config_file = 'simulation_config.json'


def test_init_empty():
    args = extract_arguments(['some/dir/init.py'])
    assert len(args) == 1
    assert args[0] == _default_config_file


def test_init_non_positional():
    with pytest.raises(ValueError):
        extract_arguments(['init.py', 'simulation_config.json'])


def test_init_config_only():
    args = extract_arguments(['another/dir/init.py',
                              '--configFile=conf/my_config.json'])
    assert len(args) == 1
    assert args[0] == 'conf/my_config.json'


def test_init_pass_options():
    args = extract_arguments(['another/dir/init.py', '--foo=bar',
                              '--configFile=conf/my_config.json',
                              '-v', '--baz=qux'])
    assert len(args) == 4
    assert args[0] == 'conf/my_config.json'
    assert args[1] == '--foo=bar'
    assert args[2] == '-v'
    assert args[3] == '--baz=qux'


def test_init_first_args():
    args = extract_arguments(['dplace', 'special' 'another/dir/init.py', '--foo=bar',
                              '--configFile=conf/my_config.json',
                              '-v', '--baz=qux'])
    assert len(args) == 4
    assert args[0] == 'conf/my_config.json'
    assert args[1] == '--foo=bar'
    assert args[2] == '-v'
    assert args[3] == '--baz=qux'


def test_init_early_config_file():
    with pytest.raises(ValueError):
        extract_arguments(['dplace', 'special', '--configFile=my_config.json', '--some=pre',
                              'etc', 'dir/init.py', '--foo=bar', '-v'])
