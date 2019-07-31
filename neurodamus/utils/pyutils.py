"""
Collection of generic Python utilities.
"""
from __future__ import absolute_import, print_function
from collections import OrderedDict
from bisect import bisect_left
from enum import EnumMeta


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)

    def __set__(self, instance, value):
        raise AttributeError("Class properties can't be override")


def dict_filter(dic, filter):
    """Creates a generator for filtering elements in a dictionary"""
    return ((key, val) for key, val in dic.items() if filter(key, val))


def dict_filter_map(dic, mapp):
    """Filters a dict and converts the keys according to a given map"""
    return {mapp[key]: val for key, val in dic.items() if key in mapp}


def docopt_sanitize(docopt_opts):
    """Sanitizes docopt parsed key names
    """
    opts = {}
    for key, val in docopt_opts.items():
        key = key.strip("<>-").replace("-", "_")
        if isinstance(val, str):
            if val.lower() in ("off", "false"):
                val = False
            elif val.lower() in ("on", "true"):
                val = True
        opts[key] = val
    return opts


class ConfigT(object):
    """ Base class for configurations.

        This class serves as a base for set of configurations.
        By inheriting and setting several class-level attributes, instances will
        be able to initialize from kwargs and dictionaries with the same keys,
        effectivelly working as validators of fields with default values.
        Furthermore, for validation of values, the attributes may be Enums.

        ```
        class RunConfig(ConfigT):
            # NOTE: Enum fields: the FIRST value is the default
            mode = Enum("Mode", "BUILD_SIMULATE BUILD_ONLY")
            model_path = None
        ```
    """
    def __init__(self, **opts):
        self._init(self, opts)

    @classmethod
    def global_init(cls, **opts):
        cls._init(cls, opts)

    @classmethod
    def _init(cls, obj, opts):
        for name, value in opts.items():
            if value is not None and not name.startswith("_") and hasattr(obj, name):
                default = getattr(obj, name)
                if type(default) is EnumMeta:
                    value = default[value]
                setattr(obj, name, value)
        # Non initialized enums set default as the first item
        for name, value in cls.__dict__.items():
            if name not in obj.__dict__ and type(value) is EnumMeta:
                setattr(obj, name, getattr(cls, name)(1))

    @staticmethod
    def _apply_f(obj, opts_dict):
        for key, val in opts_dict.items():
            setattr(obj, key, val)

    def apply(self, obj, subset=None, excludes=(), **overrides):
        """Applies the configuration to one or multiple objects (if tuple)"""
        opts = self.as_dict(subset, excludes)
        opts.update(overrides)
        if not isinstance(obj, (tuple, list)):
            obj = (obj,)
        for o in obj:
            self._apply_f(o, opts)

    def as_dict(self, subset=None, excludes=()):
        return {key: val for key, val in vars(self).items()
                if val is not None and not key.startswith("_") and
                key not in excludes and (subset is None or key in subset)}


def bin_search(container, key, keyf=None):
    """Performs binary search in a container, retrieving the index where key should be inserted
    to keep ordering. Accepts a key function to be applied to each element of the container.

    Args:
        container: The container to be searched through
        key: The key to look for
        keyf: (Optional) the function transforming container elements into comparable keys

    Returns: The position where the element is to be inserted to keep ordering.

    """
    if keyf is None:
        return bisect_left(container, key)

    binsrch_low = 0
    binsrch_high = len(container)

    while binsrch_low < binsrch_high:
        binsrch_mid = int((binsrch_low + binsrch_high) * 0.5)
        if key > keyf(container[binsrch_mid]):
            binsrch_low = binsrch_mid + 1
        else:
            binsrch_high = binsrch_mid
    return binsrch_low


class OrderedDefaultDict(OrderedDict):
    """A simple though elegant Ordered and Default dict
    """
    factory = list

    def __missing__(self, key):
        self[key] = value = self.factory()
        return value


class ConsoleColors:
    """Helper class for formatting console text.
    """
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _, DEFAULT = range(10)
    NORMAL, BOLD, DIM, UNDERLINED, BLINK, INVERTED, HIDDEN = [a << 4 for a in range(7)]

    # These are the sequences needed to control output
    _CHANGE_SEQ = "\033[{}m"
    _RESET_SEQ = "\033[0m"

    @classmethod
    def reset(cls):
        return cls._RESET_SEQ

    @classmethod
    def set_text_color(cls, color):
        return cls._CHANGE_SEQ.format(color + 30)

    @classmethod
    def format_text(cls, text, color, style=None):
        if not style:
            style = (color & 0xf0)
        color &= 0x0f
        style = style >> 4
        format_seq = "" if style is None else cls._CHANGE_SEQ.format(style)
        return format_seq + cls.set_text_color(color) + text + cls._RESET_SEQ
