import time
import functools


class ProfilerEntry:
    def __init__(self, function, args, kwargs):
        self.start_ts = time.time()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.end_ts = None
        self.internal_duration = 0

    def stop(self):
        self.end_ts = time.time()

    def add_internal_duration(self, value):
        self.internal_duration += value

    @property
    def own_duration(self):
        if self.end_ts is not None:
            return self.end_ts - self.start_ts - self.internal_duration

    @property
    def full_duration(self):
        if self.end_ts is not None:
            return self.end_ts - self.start_ts

    def __str__(self):
        call_fmt = '{}({})'.format(self.function.__name__,
                                   _format_args(self.args, self.kwargs))
        if self.end_ts is None:
            return '{}'.format(call_fmt)
        else:
            return '{} -> {:.5f}'.format(call_fmt, self.own_duration)


class Profiler:
    def __init__(self):
        self._profiling_stack = [None]
        self._dur_sum = 0
        self._dur_sqr_sum = 0
        self._calls_cnt = 0

    def profile(self, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            prev_entry = self._profiling_stack[-1]
            entry = ProfilerEntry(function, args, kwargs)
            self._profiling_stack.append(entry)
            result = function(*args, **kwargs)
            entry.stop()

            if entry.own_duration > self._average_dur + 0.5:
                print('   Average: {:.5f}'.format(self._average_dur))
                print('   Std dev: {:.5f}'.format(self._dur_std_dev))
                print('Call count: {}'.format(self._calls_cnt))
                for e in self._profiling_stack[1:]:
                    print(e)
                print()
            else:
                self._dur_sum += entry.own_duration
                self._dur_sqr_sum += entry.own_duration**2
                self._calls_cnt += 1

            self._profiling_stack.pop(-1)
            if prev_entry is not None:
                prev_entry.add_internal_duration(entry.full_duration)
            return result
        return wrapper

    @property
    def _average_dur(self):
        if not self._calls_cnt:
            return 0
        return self._dur_sum / self._calls_cnt

    @property
    def _dur_std_dev(self):
        if not self._calls_cnt:
            return 0
        return self._dur_sqr_sum / self._calls_cnt - self._average_dur**2


profile = Profiler().profile


def _format_args(args, kwargs):
    args = ', '.join(map(str, args))
    kwargs = ', '.join(
        key + '=' + str(val)
        for key, val in kwargs.items()
    )
    return ', '.join(filter(bool, [args, kwargs]))
