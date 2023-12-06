"""
Collection of generic Python utilities.
"""
import numpy as np
import weakref
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


class WeakList(list):
    def append(self, item):
        list.append(self, weakref.ref(item, self.remove))


class ConfigT(object):
    """Base class for configurations.

    This class serves as a base for set of configurations.
    By inheriting and setting several class-level attributes, instances will
    be able to initialize from kwargs and dictionaries with the same keys,
    effectively working as validators of fields with default values.
    Furthermore, for validation of values, the attributes may be Enums.

    ::\n
     class RunConfig(ConfigT):
        # NOTE: Enum fields: the FIRST value is the default
        mode = Enum("Mode", "BUILD_SIMULATE BUILD_ONLY")
        model_path = None
    """
    class _ConfigFlag:
        """A lightweith internal class to create flags"""
        __slots__ = ()

    REQUIRED = _ConfigFlag()

    def __init__(self, opt_dict=None, **opts):
        opt_dict = opt_dict or {}
        opt_dict.update(opts)
        self._init(self, opt_dict)

    @classmethod
    def set_defaults(cls, **opts):
        cls._init(cls, opts)

    @classmethod
    def _init(cls, obj, opts):
        for name, value in opts.items():
            if value is not None and not name.startswith("_") and hasattr(obj, name):
                default = getattr(obj, name)
                if type(default) is EnumMeta:
                    value = default[value]  # enum as validator
                setattr(obj, name, value)

        for name, value in cls.__dict__.items():
            if name not in obj.__dict__ and (value is cls.REQUIRED
                                             or type(value) is EnumMeta):
                raise ValueError("Config field {} is mandatory".format(name))

        setattr(obj, '_all', opts)

    # dict interface for compat
    def __setitem__(self, name, value):
        self._all[name] = value

    def __getitem__(self, name):
        return self._all[name]

    def get(self, *args):
        return self._all.get(*args)

    def __contains__(self, name):
        return name in self._all

    all = property(lambda self: self._all)

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
                if val is not None
                    and not key.startswith("_")
                    and key not in excludes
                    and (subset is None or key in subset)}


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


class ConsoleColors:
    """Helper class for formatting console text.
    """
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _, DEFAULT = range(30, 40)
    NORMAL, BOLD, DIM, UNDERLINED, BLINK, INVERTED, HIDDEN = [a << 8 for a in range(7)]

    # These are the sequences needed to control output
    _CHANGE_SEQ = "\033[{}m"
    _RESET_SEQ = "\033[0m"

    @classmethod
    def reset(cls):
        return cls._RESET_SEQ

    @classmethod
    def set_text_color(cls, color):
        return cls._CHANGE_SEQ.format(color)

    @classmethod
    def format_text(cls, text, color, style=None):
        style = (style or color) >> 8
        format_seq = str(color & 0x00ff) + ((";" + str(style)) if style else "")
        return cls._CHANGE_SEQ.format(format_seq) + text + cls._RESET_SEQ


def append_recarray(target_array, record):
    """Append a np.record to a np.recarray"""
    if target_array is None:
        target_array = np.recarray(1, dtype=record.dtype)
        target_array[0] = record
    elif not isinstance(target_array, np.recarray) or target_array.dtype != record.dtype:
        raise TypeError("Can not append a recode with a different dtype to the target array")
    else:
        nrows = target_array.shape[0]
        target_array.resize(nrows+1, refcheck=False)
        target_array[nrows] = record
    return target_array


def gen_ranges(limit, blocklen, low=0, block_increase_rate=1):
    """Generates ranges in block intervals for a given length
    block_increase_rate may be >1 in case we want the block to get increasingly large
    """
    while low < limit:
        high = min(low + blocklen, limit)
        yield low, high
        low = high
        blocklen = int(blocklen * block_increase_rate)
