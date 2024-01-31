def extract_arguments(args):
    """Get the options for neurodamus and launch it.

    We can't use positional arguments with special so we look for
    --configFile=FILE, which defaults to simulation_config.json
    """
    first_argument_pos = 1
    init_py_reached = False
    config_file = "simulation_config.json"
    for i, arg in enumerate(args):
        if not init_py_reached:
            if arg.endswith("init.py"):
                first_argument_pos = i + 1
                init_py_reached = True
            elif arg.startswith("--configFile="):
                raise ValueError("Usage: ... init.py --configFile <config_file.json> ...")
            continue

        elif not arg.startswith("-"):
            raise ValueError("Positional arguments are not supported by init.py. "
                             f"Found positional argument: '{arg}'")
        elif arg.startswith("--configFile="):
            config_file = arg.split('=')[1]

    result_args = ([config_file] +
                   [x for x in args[first_argument_pos:] if not x.startswith("--configFile=")])
    return result_args
