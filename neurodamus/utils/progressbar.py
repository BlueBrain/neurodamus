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


class ProgressBar(object):
    """ProgressBar class holds the options of the progress bar.
    """
    def __init__(self, start=0, end=10, width=60, fill='=', blank='.',
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
        self.progress = .0
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

    __repr__ = __str__

    def reset(self):
        """Resets the current progress to the start point"""
        self.progress = self._start
        return self


class AnimatedProgressBar(ProgressBar):
    """Extends ProgressBar to allow you to use it straighforward on a script.
    Accepts an extra keyword argument named `stdout` (by default use sys.stdout)
    and may be any file-object to which send the progress status.
    """
    def __init__(self, *args,  **kwargs):
        super(AnimatedProgressBar, self).__init__(*args, **kwargs)
        self._stream = kwargs.get('stdout', sys.stdout)
        self._prev_bar_len = 0
        self._tty_mode = hasattr(self._stream, 'isatty') and self._stream.isatty()
        if not self._tty_mode:
            self._width = 50
            self._stream.write('|-------20%-------40%-------60%-------80%------100%|\n|')

    def show_progress(self):
        if self._tty_mode:
            self._stream.write('\r')
            self._stream.write(str(self))
        else:
            self._show_incremental_bar()
        self._stream.flush()

    def _show_incremental_bar(self):
        bar_len = self.cur_width
        if bar_len > self._prev_bar_len:
            self._stream.write('#' * (bar_len - self._prev_bar_len))
            self._prev_bar_len = bar_len

    def __del__(self):
        # Since some streams might not support \r we finish the bar
        if not self._tty_mode:
            self._show_incremental_bar()
        out_str = "[Done] Time taken: %d sec." % (time.time() - self._init_time)
        self._stream.write("\r{}{}\n".format(out_str, " "*(self._width + 8 - len(out_str))))


if __name__ == '__main__':
    p = AnimatedProgressBar(end=100, width=80)

    while p.progress < 100:
        p += 5
        p.show_progress()
        time.sleep(0.1)

    for i in range(80, -1, -20):
        time.sleep(0.5)
        p.progress = i
        p.show_progress()
