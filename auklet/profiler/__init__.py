from __future__ import absolute_import

import time

from auklet.base import Runnable, frame_stack, Client
from auklet.stats import AukletProfileTree
from auklet.profiler.sampling import AukletSampler


__all__ = ['Profiler', 'SamplingProfiler']


class Profiler(Runnable):
    """The base class for profiler."""

    def start(self):
        self._cpu_time_started = time.clock()
        self._wall_time_started = time.time()
        return super(Profiler, self).start()

    def frame_stack(self, frame):
        return frame_stack(frame)

    def result(self):
        """Gets the frozen statistics to serialize by Pickle."""
        try:
            cpu_time = max(0, time.clock() - self._cpu_time_started)
            wall_time = max(0, time.time() - self._wall_time_started)
        except AttributeError:
            cpu_time = wall_time = 0.0
        return 0, cpu_time, wall_time


class SamplingProfiler(Profiler):
    #: The frames sampler.  Usually it is an instance of :class:`profiling.
    #: sampling.samplers.Sampler`.
    sampler = None
    profiler_tree = None

    def __init__(self, apikey=None, app_id=None, base_url=None):
        client = Client(apikey, app_id, base_url)
        self.profiler_tree = AukletProfileTree()
        sampler = AukletSampler(client, self.profiler_tree)
        super(SamplingProfiler, self).__init__()
        self.sampler = sampler

    def sample(self, frame, event):
        """Samples the given frame."""
        increment_call = False
        if event == "call":
            increment_call = True
        stack = [(frame, increment_call)]
        frame = frame.f_back
        while frame:
            stack.append((frame, False))
            frame = frame.f_back
        self.profiler_tree.update_hash(stack)

    def run(self):
        self.sampler.start(self)
        yield
        self.sampler.stop()
