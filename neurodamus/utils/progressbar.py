"""
Classes to represent a task's progress in the form of a progress bar.

Here is some basic usage with the default options:

    >>> from progressbar import ProgressBar
    >>> p = ProgressBar()
    >>> print p
    [>............] 0%
    >>> p + 1
    >>> print p
    [=>...........] 10%
    >>> p + 9
    >>> print p
    [============>] 0%

And here another example with different options:

    >>> from progressbar import ProgressBar
    >>> custom_options = {
    ...     'end': 100,
    ...     'width': 20,
    ...     'fill': '#',
    ...     'format': '%(progress)s%% [%(fill)s%(blank)s]'
    ... }
    >>> p = ProgressBar(**custom_options)
    >>> print p
    0% [....................]
    >>> p + 5
    >>> print p
    5% [#...................]
    >>> p + 9
    >>> print p
    100% [####################]
"""
from __future__ import print_function
import sys
import time
from itertools import islice


class Progress(object):
    """Progress class holds the progress information.

    It can be queried for the current progress, and overloads __repr__ for a simple display.
    It can be managed manually, via '+=' and -= operators, or automatically by consuming
    iterables.
    """

    def __init__(self, end, start=0, **kw):
        """ Creates a progress bar

        Args:
            end:   State in which the progress has terminated. False for unknown (-> spinner)
            start: State from which start the progress. For example, if start is
                   5 and the end is 10, the progress of this state is 50%
        """
        if start < 0 or (end is not False and start > end):
            raise ValueError("Invalid Start value. Must be a non-negative smaller than end")
        self._start = start
        self._end = end
        self._init_time = time.time()
        self.reset()

    def __iadd__(self, increment):
        self.progress += increment
        if self._end is not False:
            self.progress = min(self._end, self.progress)
        return self

    def __isub__(self, decrement):
        self.progress = max(self._start, self.progress - decrement)
        return self

    @property
    def completion_ratio(self):
        try:
            return float(self.progress - self._start) / self._end
        except ZeroDivisionError:
            if self._end is False:
                return False
        return 1.0

    def __repr__(self):
        total = "N.A." if self._end is False else str(self._end)
        return "<Progress: %d/%s>" % (self.progress, total)

    def reset(self):
        """Resets the current progress to the start point"""
        self.progress = self._start

    def _set_progress(self, val):
        self._progress = val

    progress = property(lambda self: self._progress, _set_progress)

    @property
    def time_taken(self):
        return time.time() - self._init_time

    def __call__(self, iterable, end=None, start=0):
        for elem in islice(iterable, start, end):
            yield elem
            self.__iadd__(1)

    # Helpers to monitor/show progress while consuming an iterable
    # ------------------------------------------------------------
    @classmethod
    def iter(cls, iterable, end=None, start=0, **kw):
        """Consumes (a slice of) an iterable.

        Args:
            iterable: the iterable to consume and monitor progress
            end: The end index. Alternatively None will automatically detect size,
                 while False instructs to not compute size -> spinner
            start: in which position to start iterating
        """
        if end is None:
            try: end = len(iterable)
            except TypeError: end = False
        # __call__ 'end' cant be False -> None
        return cls(end, start, **kw)(iterable, end or None, start)

    @classmethod
    def itervalues(cls, iterable, **kw):
        return cls.iter(iterable.values(), len(iterable), **kw)

    @classmethod
    def iteritems(cls, iterable, **kw):
        return cls.iter(iterable.items(), len(iterable), **kw)


class ProgressBar(Progress):
    """ProgressBar implements a fully visual text-based representation of a progress.
    and may be any file-object to which send the progress status.
    """
    _no_tty_bar = "-------20%-------40%-------60%-------80%------100%"  # len 50

    def __init__(self, end, start=0, width=60, fill='=', blank='.', stream=sys.stdout,
                 clear=None, fmt='[%(fill)s>%(blank)s] %(progress)s', tty_bar=None, name=''):
        """
        Args:
            end:   State in which the progress has terminated. False for unknown (-> spinner)
            start: State from which start the progress. For example, if start is
                   5 and the end is 10, the progress of this state is 50%
            width: bar length
            fill:  String to use for "filled" used to represent the progress
            blank: String to use for "filled" used to represent remaining space.
            stream: the destination stream (default: stdout),
            clear: whether to clear the current line or keep time info (and add '\n')
            fmt: Bar format string
            tty_bar: Controls whether the bar should be enhanced for text terminals.
                Default: None (auto-detect), False, True
        """
        self._tty_mode = ((hasattr(stream, 'isatty') and stream.isatty())
                          if tty_bar is None else tty_bar)
        self._width = width if self._tty_mode else 50
        self._fill = fill
        self._blank = blank
        self._format = fmt + " "
        self._stream = stream
        self._clear = self._tty_mode if clear is None else clear
        self._prev_bar_len = None
        self._name = name
        super(ProgressBar, self).__init__(end, start)

    def _bar_len_progress(self):
        if self._end is not False:
            ratio = self.completion_ratio
            return int(self._width * ratio), "{}%".format(int(ratio * 100))
        else:
            return self.progress % self._width, str(self.progress)

    def __str__(self):
        bar_len, progress = self._bar_len_progress()
        fill = self._fill * bar_len
        blank = self._blank * (self._width - bar_len)
        return self._name + self._format % {'fill': fill, 'blank': blank, 'progress': progress}

    def show_progress(self):
        if self._end == 0:
            return
        if self._tty_mode:
            self._stream.write('\r' + str(self))
        else:
            self._show_incremental_bar()
        self._stream.flush()

    def _show_incremental_bar(self):
        bar_len, _ = self._bar_len_progress()
        if self._prev_bar_len is None or bar_len < self._prev_bar_len:
            # We need to produce a new bar.
            self._stream.write("\r{}|".format(self._name))
            self._prev_bar_len = 0

        if bar_len > self._prev_bar_len:
            self._stream.write(self._no_tty_bar[self._prev_bar_len:bar_len])
            self._prev_bar_len = bar_len

    def __del__(self):
        if not self._tty_mode:
            # Complete progressbar
            self._show_incremental_bar()

        if self._clear:
            self._stream.write("\r{}\r".format(" " * (self._width + 8 + len(self._name))))
        else:
            # Output a nice stat about time taken
            self._stream.write("| [Time taken: {:.2f} s]\n".format(self.time_taken))

    def _set_progress(self, val):
        Progress._set_progress(self, val)
        self.show_progress()

    progress = property(lambda self: self._progress, _set_progress)


# ------------------------
# QUICK TESTING
# ------------------------

if __name__ == '__main__':
    p = ProgressBar(100, width=80)

    while p.progress < 100:
        time.sleep(0.1)
        p += 5

    for i in range(80, -1, -20):
        time.sleep(0.5)
        p.progress = i

    del p

    # progressbars can also be used as a consumer-generators to monitor loop progress
    l1 = range(0, 100, 10)

    for j in ProgressBar.iter(l1):
        # Do something with j
        time.sleep(0.2)

    # Instances can also consume, be reused, and work with sub-selection
    # It is the user responsability to initialize with the right number of iterations
    bar = ProgressBar(15)
    l2 = range(100, 200, 10)
    for x in bar(l1):
        time.sleep(0.2)
    l2 = [x for x in bar(l2, 5)]
    assert l2 == [100, 110, 120, 130, 140]

    # Alternativelly, if unknown, use False (creates a spinner)
    bar = ProgressBar(False)
    for x in bar(l1):
        time.sleep(0.2)
    for y in bar(range(60)):
        time.sleep(0.04)
