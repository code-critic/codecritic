from optparse import OptionParser
from random import randint
import random
import sys
import io
import queue
#import statprof
from contextlib import contextmanager




#@contextmanager
#def stat_profiler():
    #statprof.start()
    #yield  statprof
    #statprof.stop()
    #statprof.display()

class Edge:
    def __init__(self, i, u, v, cap, flux=0):
        self.i = i
        self.u = u
        self.v = v
        self.cap = cap
        self.flux = flux
        self.res_cap = cap
        self._inv = None

    # @property
    # def res_cap(self):
    #     return self.cap - self.flux


class Network:
    def __init__(self, in_stream):
        self.read(in_stream)

    def read(self, in_stream):
        n_source, n_sink, n_junction, n_edges = [int(v) for v in in_stream.readline().split()]
        self.n_vtx = n_source + n_junction + n_sink
        sources = range(0, n_source)
        cap_sources = [ int(in_stream.readline()) for _ in range(n_source)]
        self.total_source = sum(cap_sources)
        edges = [ in_stream.readline().split() for s in range(n_edges)]
        self.source_vtx = self.n_vtx
        self.sink_vtx = self.n_vtx + 1
        self.n_vtx += 2
        self.vtk = [[] for _ in range(self.n_vtx)]
        self.max_cap = 0
        for e_line in edges:
            v_in, v_out, cap = [int(v) for v in e_line]
            self.add_edge(v_in, v_out, cap, cap)
            self.max_cap += cap
        for v_out, cap in zip(sources, cap_sources):
            self.add_edge(self.source_vtx, v_out, cap, 0)
        #self.set_reverse_edges()

    def reinit(self):
        # remove sink edges
        for e in reversed(self.vtk[self.sink_vtx]):
            self.rm_edge(e)
        # zero fluxes
        for u_edges in self.vtk:
            for e in u_edges:
                e.flux = 0
                e.res_cap = e.cap

    def add_sinks(self, sinks):
        for v_in in sinks:
            self.add_edge(v_in, self.sink_vtx, self.total_source, 0)

    # def set_reverse_edges(self):
    #     for v_list in self.vtk:
    #         for uv in v_list:
    #             # find reverse edge
    #             for vu in self.vtk[uv.v]:
    #                 if vu.v == uv.u:
    #                     uv.inv = vu.i
    #                     uv.inv = vu.i
    #                     break
    #             else:
    #                 vu = self.add_edge(uv.v, uv.u, 0)
    #                 uv.inv = vu.i
    #                 vu.inv = uv.i

    def add_edge(self, v_in, v_out, cap_uv, cap_vu):
        uv = Edge(len(self.vtk[v_in]), v_in, v_out, cap_uv)
        vu = Edge(len(self.vtk[v_out]), v_out, v_in, cap_vu)
        self.vtk[v_in].append(uv)
        self.vtk[v_out].append(vu)
        uv.inv = vu.i
        vu.inv = uv.i
        return uv

    def rm_edge(self, uv):
        i, j = uv.i, uv.inv
        self.vtk[uv.u].pop(i)
        self.vtk[uv.v].pop(j)

    @property
    def n_sources(self):
        return len(self.vtk[self.source_vtx])

    @property
    def max_flux(self):
        src_sum = sum([e.flux  for e in self.vtk[self.source_vtx]] )
        sink_sum = sum([-e.flux for e in self.vtk[self.sink_vtx]])
        #assert src_sum == sink_sum
        return src_sum

    def send_flux(self, uv, flux):
        vu = self.vtk[uv.v][uv.inv]
        # print(uv.u, uv.v, uv.flux, uv.cap)
        uv.flux += flux
        uv.res_cap -= flux
        vu.flux -= flux
        vu.res_cap += flux

    def find_and_improve_path(self, net, source_vtx, sink_vtx):

        #BFS
        distance = self.n_vtx * [ None ]
        previous = distance.copy()
        q = queue.Queue()

        u = source_vtx
        q.put(u)
        distance[u] = 0
        while not q.empty():
            u = q.get()
            d = distance[u]
            if u == sink_vtx:
                break
            for uv in net[u]:
                v = uv.v
                if uv.res_cap > 0 and distance[v] is None:
                    q.put(v)
                    distance[v] = d + 1
                    previous[v] = uv
        else:
            # No improvement path
            return False

        # Improve
        min_cap = self.max_cap
        e_list = []
        while True:
            uv = previous[u]
            if uv is None:
                break
            u = uv.u
            min_cap = min(min_cap, uv.res_cap)
            e_list.append(uv)

        #print("Improve path: + ", min_cap)
        for uv in e_list:
            self.send_flux(uv, min_cap)


        #print("Total flux: ", self.max_flux)
        return True

    def max_flux_edmons_karp(self):
        while self.find_and_improve_path(self.vtk, self.source_vtx, self.sink_vtx):
            pass
        return self.max_flux


    def max_flux_dinic(self):
        pass

    def max_flux_dinic(self):
        pass


    def make_result_sources(self):
        if self.max_flux == self.total_sink:
            return [e.flux for e in self.vtk[self.source_vtx]]
        else:
            return [0 for _ in range(self.n_sources)]


def solve(in_stream, out_stream):
    net = Network(in_stream)
    n_cases = int(in_stream.readline())
    for _ in range(n_cases):
        #print("====")
        net.reinit()
        sinks = [int(v) for v in in_stream.readline().split()]
        net.add_sinks(sinks)
        max_flux = net.max_flux_edmons_karp()
        out_stream.write("{}\n".format(max_flux))



def make_data(in_stream, problem_size):
    '''
    1. Generate square grid graph with diagonal edges.
    2. Assign capacities random ints 0-5.
    '''
    import numpy as np

    # random texture in range 0, 1024

    n_vtxs = problem_size * problem_size
    n_sources = problem_size
    n_junctions = problem_size * (problem_size - 2)
    n_sinks = problem_size
    edges = []
    dxy = [ (dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0) ]

    for ix in range(problem_size):
        for iy in range(problem_size):
             for dx, dy in dxy:
                jx, jy = ix + dx, iy + dy
                if 0 <= jx < problem_size and 0 <= jy < problem_size:
                    cap = randint(0, 50)
                    u = iy * problem_size + ix
                    v = jy * problem_size + jx
                    if u < v:
                        edges.append((u, v, cap))
    sources = [ randint(1, 100) for _ in range(n_sources)]
    sinks  = list(range(n_sources, n_sources + n_sinks))
    problem_setup = io.StringIO()
    problem_setup.write("{} {} {} {}\n".format(n_sources, n_sinks, n_junctions, len(edges)))
    for s in sources:
        problem_setup.write("{}\n".format(s))
    for e in edges:
        problem_setup.write("{} {} {}\n".format(*e))
    n_cases = 2 + int(np.log(problem_size))
    n_case_sinks = 3
    problem_setup.write("{}\n".format(n_cases))
    for _ in range(n_cases):
        selection = np.random.choice(sinks, size=n_case_sinks, replace=False)
        problem_setup.write("{} {} {}\n".format(*selection))



    sys.stdout.write(problem_setup.getvalue())

    out_stream = io.StringIO()
    problem_setup.seek(0)
    solve(problem_setup, out_stream)
    #print("====")
    sys.stderr.write(out_stream.getvalue())
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
