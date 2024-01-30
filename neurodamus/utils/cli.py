

def extract_arguments(args):
    """Get the options for neurodamus and launch it.

    We can't use positional arguments with special so we look for
    --configFile=FILE, which defaults to simulation_config.json
    """
    config_file = "simulation_config.json"
    for i, arg in enumerate(args[1:]):
        if not arg.startswith("-"):
            raise ValueError("Positional arguments are not supported")
        elif arg.startswith("--configFile="):
            config_file = arg.split('=')[1]
            break
    args = [config_file] + [x for x in args[1:] if not x.startswith("--configFile=")]
    return args
