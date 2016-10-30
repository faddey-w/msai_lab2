import time
import weakref


class Animator:

    FRAMES_PER_SECOND = 15

    def __init__(self, check_closed, delay_apply):
        self._is_closed = check_closed
        self._delay_apply = delay_apply
        self._entries = []
        self._worker_id = None
        # it seems that Tk.after() accepts only raw functions, not methods
        self._worker_caller = lambda: self._worker()

    def __call__(self, function, start_val, stop_val, duration, callback=None):
        if self._worker_id is None:
            self._schedule_worker()
        self._entries.append(self._Entry(
            function, start_val, stop_val,
            duration, callback
        ))

    def _worker(self):
        # check if we should stop
        if self._is_closed() or not self._entries:
            self._worker_id = None
            return
        # here we provide the safe way to add new animations
        # from within callbacks or step functions
        remove_indices = set()
        entry_dict = dict(enumerate(self._entries))
        self._entries.clear()

        # perform all animation steps within single event of event-loop
        # that's why this class was created:
        # all animations will be rendered to the display at once
        # instead of touching the slow display after each step
        for idx, entry in entry_dict.items():
            ts = time.time() * 1000
            ratio = (ts - entry.start_ts) / entry.duration
            start, stop = entry.start_val, entry.stop_val
            if ratio <= 1:
                entry.function(start + ratio * (stop-start))
            else:
                entry.function(stop)
                remove_indices.add(idx)
                if entry.callback:
                    entry.callback()
        # remove finished animations
        for idx in remove_indices:
            entry_dict.pop(idx)
        # put pending animations into the list again
        # note that self._entries may be not empty at that point
        self._entries.extend(entry_dict.values())

        #
        self._schedule_worker()

    class _Entry:
        def __init__(self, function, start_val, stop_val, duration, callback):
            self.function = function
            self.start_val = start_val
            self.stop_val = stop_val
            self.duration = duration
            self.callback = callback
            self.start_ts = time.time() * 1000

    def _schedule_worker(self):
        period = 1000 // self.FRAMES_PER_SECOND
        w_id = self._delay_apply(period, self._worker_caller)
        self._worker_id = w_id


class CallbackJoiner:
    """
    Calls real callback when all callbacks previously
    created by .make_callback() gets called. Reusable.

    >>> def real_callback():
    ...     print('Hello there')
    ...
    >>> joiner = CallbackJoiner(real_callback)
    >>> cb1 = joiner.make_callback()
    >>> cb2 = joiner.make_callback()
    >>> cb3 = joiner.make_callback()
    >>> cb1()
    >>> cb2()
    >>> cb3()
    Hello there
    >>> cb1 = joiner.make_callback()
    >>> cb1()
    Hello there
    >>>
    """

    def __init__(self, real_callback):
        self._real_callback = real_callback
        self._counter = 0
        self._call_ids = weakref.WeakValueDictionary()

    def _callback(self, call_id):
        self._call_ids.pop(call_id, None)
        if not self._call_ids:
            self._real_callback()

    def make_callback(self):
        # put ID value into closure to mane it constant
        counter = self._counter
        self._counter += 1
        cb = lambda: self._callback(counter)
        self._call_ids[counter] = cb
        return cb
