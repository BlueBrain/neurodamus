#!/usr/bin/env python
"""
progressbar.py

A Python module with a ProgressBar class which can be used to represent a
task's progress in the form of a progress bar and it can be formated in a
basic way.

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
    """ProgressBar class holds the options of the progress bar.
    """
    def __init__(self, end, start=0, width=60, fill='=', blank='.',
                 format='[%(fill)s>%(blank)s] %(progress)s%%'):
        """ Creates a progress bar

        Args:
            start: State from which start the progress. For example, if start is
                   5 and the end is 10, the progress of this state is 50%
            end:   State in which the progress has terminated.
            width: bar length
            fill:  String to use for "filled" used to represent the progress
            blank: String to use for "filled" used to represent remaining space.
            format: Bar format
        """
        self._start = start
        self._end = end
        self._width = width
        self._fill = fill
        self._blank = blank
        self._format = format + " "
        self._init_time = time.time()
        self.reset()

    def __iadd__(self, increment):
        self.progress = min(self._end, self.progress + increment)
        return self

    def __isub__(self, decrement):
        self.progress = max(self._start, self.progress - decrement)
        return self

    @property
    def cur_width(self):
        return int(float(self.progress) * self._width / self._end)

    def __str__(self):
        cur_width = self.cur_width
        fill = self._fill * cur_width
        blank = self._blank * (self._width - cur_width)
        percentage = int(self.progress * 100.0 / self._end)
        return self._format % {'fill': fill, 'blank': blank, 'progress': percentage}

    def __repr__(self):
        return "<Progress: %d/%d>" % (self.progress, self._end)

    def reset(self):
        """Resets the current progress to the start point"""
        self.progress = self._start

    def __call__(self, iterable, start=0, stop=None):
        self.progress = start
        for elem in islice(iterable, start, stop):
            yield elem
            self.__iadd__(1)

    def _set_progress(self, val):
        self._progress = val

    progress = property(lambda self: self._progress, _set_progress)


class ProgressBar(Progress):
    """Extends ProgressBar to allow you to use it straighforward on a script.
    Accepts an extra keyword argument named `stdout` (by default use sys.stdout)
    and may be any file-object to which send the progress status.
    """
    _no_tty_bar = "-------20%-------40%-------60%-------80%------100%"  # len 50

    def __init__(self, end, **kwargs):
        self._stream = kwargs.get('stdout', sys.stdout)
        self._prev_bar_len = 0
        self._tty_mode = hasattr(self._stream, 'isatty') and self._stream.isatty()
        if not self._tty_mode:
            self._stream.write('|')
            kwargs["width"] = 50
        super(ProgressBar, self).__init__(end, **kwargs)

    def show_progress(self):
        if self._tty_mode:
            self._stream.write('\r')
            self._stream.write(str(self))
        else:
            self._show_incremental_bar()
        self._stream.flush()

    def _show_incremental_bar(self):
        bar_len = self.cur_width
        if bar_len < self._prev_bar_len:
            # We need to produce a new bar.
            self._stream.write("\r|")
            self._prev_bar_len = 0

        if bar_len > self._prev_bar_len:
            self._stream.write(self._no_tty_bar[self._prev_bar_len:bar_len])
            self._prev_bar_len = bar_len

    def __del__(self):
        # Since some streams might not support \r we finish the bar
        if not self._tty_mode:
            self._show_incremental_bar()
        out_str = "[Done] Time taken: %d sec." % (time.time() - self._init_time)
        self._stream.write("\r{}{}\n".format(out_str, " "*(self._width + 8 - len(out_str))))

    def _set_progress(self, val):
        Progress._set_progress(self, val)
        self.show_progress()

    progress = property(lambda self: self._progress, _set_progress)


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
    p = ProgressBar(len(l1))

    for j in p(l1):
        # Do something with j
        time.sleep(0.2)

    # Can be reused and work even in comprehension, and sub-selection
    l2 = [time.sleep(0.2) for x in p(l1, 5)]
