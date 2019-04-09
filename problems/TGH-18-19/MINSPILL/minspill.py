from optparse import OptionParser
from random import randint
import random
import sys
import io
import numpy as np
#import statprof
#from contextlib import contextmanager
import heapq


#@contextmanager
#def stat_profiler():
    #statprof.start()
    #yield  statprof
    #statprof.stop()
    #statprof.display()


class State:
    def __init__(self, i, j, spill):
        self.i, self. j = i, j
        self.spill = spill

class ImplicitDijkstra:
    def __init__(self, in_stream):
        n_containers = int(in_stream.readline())
        self.volumes = [int(in_stream.readline()) for _ in range(n_containers)]

        self.states = {}
        self.queue = []


    def pour(self, volumes, cost, i, j):
        new_volumes  = list(volumes)
        free = self.volumes[j] - new_volumes[j]
        spill = min(free, new_volumes[i])
        new_volumes[i] -= spill
        new_volumes[j] += spill
        new_volumes = tuple(new_volumes)
        new_state = State(i, j, spill)
        self.add(new_volumes, new_state, cost + spill)

    def add(self, new_volumes, new_state, new_cost):
        if new_volumes not in self.states:
            self.states[new_volumes] = new_state
            heapq.heappush(self.queue, (new_cost, new_volumes))
            # check and save results
            if self.results[new_volumes[new_state.i]] is None:
                self.results[new_volumes[new_state.i]] = new_volumes
                self.n_results += 1

            if self.results[new_volumes[new_state.j]] is None:
                self.results[new_volumes[new_state.j]] = new_volumes
                self.n_results += 1

    def run_dijkstra(self):
        i_fill = max(range(len(self.volumes)), key=self.volumes.__getitem__)
        self.results = (self.volumes[i_fill] + 1) * [None]
        self.n_results = 0

        volumes = len(self.volumes) * [0]
        volumes[i_fill] = self.volumes[i_fill]
        volumes = tuple(volumes)
        state = State(i_fill, i_fill, self.volumes[i_fill])
        self.add(volumes, state, 0)

        while self.queue and self.n_results < len(self.results):
            cost, volumes = heapq.heappop(self.queue)
            state = self.states[volumes]
            for l in [state.i, state.j]:
                for k in range(len(self.volumes)):
                    if k != state.i and k != state.j:
                        self.pour(volumes, cost, l, k)
                        self.pour(volumes, cost, k, l)
        sys.stderr.write("#states: {}\n".format(len(self.states)))

    def get_path(self, volumes):
        path = []
        cost = 0
        state = self.states[tuple(volumes)]
        while state.i != state.j:
            path.append((state.i, state.j))
            cost += state.spill
            volumes[state.i] += state.spill
            volumes[state.j] -= state.spill
            state = self.states[tuple(volumes)]
        return list(reversed(path)), cost

    def output_results(self, stream):
        for vol, res in enumerate(self.results[1:]):
            if res is None:
                stream.write("{} {} {}\n".format(vol+1, -1, -1))
            else:
                path, cost = self.get_path(list(res))
                stream.write("{} {} {}\n".format(
                    vol+1, cost, len(path)))
                # for i,j in path:
                #     stream.write("    {}>{}\n".format(i, j))

def solve(in_stream, out_stream):
    dijkstra = ImplicitDijkstra(in_stream)
    dijkstra.run_dijkstra()
    dijkstra.output_results(out_stream)


def make_data(in_stream, problem_size):
    size = problem_size
    max_vol = int( size ** 0.3)
    volumes = []
    while size > 2:
        vol = randint(2, max_vol)
        volumes.append(vol)
        size = size / vol
    problem_setup = io.StringIO()
    problem_setup.write("{}\n".format(len(volumes)))
    for v in volumes:
        problem_setup.write("{}\n".format(v))

    #sys.stdout.write(problem_setup.getvalue())
    #print("====")
    out_stream = io.StringIO()
    problem_setup.seek(0)
    solve(problem_setup, out_stream)

    #sys.stderr.write(out_stream.getvalue())
    #print("====")

    #res_stream = StringIO.StringIO()
    #segment.image_to_stream(res_stream, head=False)
    #assert (out_stream.getvalue() == res_stream.getvalue())

    in_stream.write(problem_setup.getvalue())


'''
Main script body.
'''

parser = OptionParser()
parser.add_option("-p", "--problem-size", dest="size", help="Problem size.", default=None)
parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None)
parser.add_option("-r", dest="rand", default=False, help="Use non-deterministic algo")

options, args = parser.parse_args()


if options.rand:
    random.seed(options.rand)
else:
    random.seed(options.size)

if options.size is not None:
    make_data(sys.stdout, int(options.size))
else:
    solve(sys.stdin, sys.stdout)
