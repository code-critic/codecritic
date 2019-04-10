#!/usr/bin/env python

from optparse import OptionParser
import json
import time
import sys
import io
#import numpy as np
#import networkx as nx
#import matplotlib.pyplot as plt



# Solution time limit in seconds.
TIME_LIMIT = 360

class Vertex :
    def __init__(self, idx):
        self.idx = idx
        self.adj = set()
        self.color = None
        #self.n_used_colors = 0  # Number of different colors of neighbors.

# global variables
class Colouring :

    def __init__(self, in_stream) :
        self.vertices = []
        self.n_colors = None
        self.colors_history = []
        # A stack to remember sequence of vertex colorings.
        self.neighbour_colors = None
        # At position [i, j] number of neigbours of vtx 'i' using color 'j'.
        self.graph_from_stream(in_stream)
        # Read application dependend graph. TODO: We should move this out of the class.

        self.neighbour_colors = [ [0]*self.n_colors for _ in self.vertices ]
        # Table to mark how many times is every color used in neighbors.
        self.vtx_degs = [len(vtx.adj) for vtx in self.vertices]
        self.max_deg = max(self.vtx_degs) + 1
        self.max_deg_scale = [self.max_deg] * len(self.vertices)


        self.n_colorings = 0
        # Count total number of colorings, total number of yields.
        self.n_branching = 0
        self.color_first_use = self.n_colors * [None]
        # Mark which vtx first used the color.

    def add_clique(self, i_vertices):
        for i in i_vertices:
            for j in i_vertices:
                self.vertices[i].adj.add(j)

    def graph_from_stream(self, in_stream):
        n_students, n_subjs, n_teachers, n_blocks =  [ int(val) for val in in_stream.readline().split() ]
        #print("st: %d sub: %d teach: %d blocks: %d\n"%(n_students, n_subjs, n_teachers, n_blocks))
        self.vertices = [ Vertex(i) for i in range(n_subjs) ]

        for st in range(n_students):
            subjs = [ int(val) for val in in_stream.readline().split() ]
            self.add_clique(subjs)

        subjs_for_teacher = [ [] for i in range(n_teachers) ]
        for subj in range(n_subjs):
            teacher = int(in_stream.readline())
            subjs_for_teacher[teacher].append(subj)

        for teacher_list in subjs_for_teacher:
            self.add_clique(teacher_list)

        self.n_colors = n_blocks
        for vtx in self.vertices:
            vtx.adj = list(vtx.adj)
        # Graph edges are for intersecting groups of subject's participants

    @staticmethod
    def canonic_coloring(old_coloring):
        """
        Check that all vertices are colored and renumber colors.
        Canonic coloring is such that we take sequence of colors sorted by vertex numbers.
        take only first appearance of every color and resulting sequence has to be sorted.
        :return:
        """
        coloring = []
        old_to_new={}
        for c in old_coloring:
            new_col = old_to_new.get(c, len(old_to_new))
            old_to_new[c] = new_col
            coloring.append(new_col)
        return coloring


    def make_colouring(self, yield_every_iter=False):
        """
        Color next vtx.
        :yield: Coloring if all vtxs are colored, None for other iter.
        :return:  All colorings checked.
        """
        while True:
            if len(self.colors_history) == len(self.vertices):
                # all colored
                coloring = [vtx.color for vtx in self.vertices]
                self.n_colorings += 1
                #return Colouring.canonic_coloring(coloring)
                yield Colouring.canonic_coloring(coloring)
                if not self.revert():
                   return
            else:
                # partial coloring
                i_vtx, n_used_colors = self.find_vtx_to_color()
                if n_used_colors == self.n_colors:
                    # Saturated vertex, we must backtrace
                    if not self.revert():
                        return
                else:
                    self.color_vtx(i_vtx, 0)
            if yield_every_iter:
               yield None



    def check_consistency(self):
        for vtx in self.vertices:
            colors = [0] * self.n_colors
            for ngh in vtx.adj:
                if self.vertices[ngh].color is not None:
                    colors[self.vertices[ngh].color] +=1
            assert colors == self.neighbour_colors[vtx.idx]

    def mark_neighbors(self, i_vtx, color):
        self.vertices[i_vtx].color = color
        self.vtx_degs[i_vtx] = 0
        self.max_deg_scale[i_vtx] = 0
        adj = self.vertices[i_vtx].adj
        for v_adj in adj:
            self.neighbour_colors[v_adj][color] += 1
        #self.check_consistency()
        #self.n_used_colors[]
        #    if self.neighbour_colors[ngb, color] == 1:
        #        self.vertices[ngb].n_used_colors += 1

    def unmark_neighbors(self, i_vtx, color):
        self.vertices[i_vtx].color = None
        self.vtx_degs[i_vtx] = len(self.vertices[i_vtx].adj)
        self.max_deg_scale[i_vtx] = self.max_deg
        adj = self.vertices[i_vtx].adj
        for v_adj in adj:
            self.neighbour_colors[v_adj][color] -= 1
        #self.check_consistency()
            #if self.neighbour_colors[ngb, color] == 0:
            #    self.vertices[ngb].n_used_colors -= 1

    # def full_find_vtx(self):
    #     i_vtx = None
    #     max_sat = 0
    #     max_deg = 0
    #     for vtx in self.vertices:
    #         if vtx.color is not None:
    #             continue
    #         colors = np.zeros(self.n_colors)
    #         for ngh in vtx.adj:
    #             if self.vertices[ngh].color is not None:
    #                 colors[self.vertices[ngh].color] +=1
    #         n_used = np.count_nonzero(colors)
    #         assert np.all( colors == self.neighbour_colors[vtx.idx, :] ), (colors, self.neighbour_colors[vtx.idx, :])
    #         if  n_used > max_sat or n_used == max_sat and len(vtx.adj) > max_deg:
    #             i_vtx = vtx.idx
    #             max_sat = n_used
    #             max_deg = len(vtx.adj)
    #     if i_vtx is None:
    #         i_vtx = 0
    #         max_sat = self.n_colors
    #     return (i_vtx, max_sat)

    def find_vtx_to_color(self):
        n_used_colors = [ sum([v!=0 for v in nc]) for nc in self.neighbour_colors]
        costs = [ndeg * ncol + vdeg for ndeg, ncol, vdeg in zip(self.max_deg_scale, n_used_colors, self.vtx_degs)]
        from operator import itemgetter
        i_vtx, max_cost = max(enumerate(costs), key=itemgetter(1))
        max_sat = n_used_colors[i_vtx]
        #full_res = self.full_find_vtx()
        res = (i_vtx, max_sat)
        #assert res == full_res, (res, full_res)
        return res

    def color_vtx(self, i_vtx, next_color):
        """
        :param i_vtx: Vertex to color.
        :param color: Last used color, use next one.
        :return: pair to store in history or None if no other color exists.
        """
        assert self.vertices[i_vtx].color is None, (i_vtx, self.vertices[i_vtx].color)
        usage_of_color = self.neighbour_colors[i_vtx]
        color = next_color
        while color < self.n_colors and usage_of_color[color] > 0:
            color += 1
        if color < self.n_colors:
            # color vertex and mark colorign to neighbors
            self.n_branching += 1
            self.mark_neighbors(i_vtx, color)

            if self.color_first_use[color] is None:
                # If color is first used by this vertex, stick with this color through backtracking.
                self.color_first_use[color] = i_vtx
                self.colors_history.append((i_vtx, color, self.n_colors))
            else:
                self.colors_history.append((i_vtx, color, color + 1))

            self.i_vtx = i_vtx + 1
            return True
        else:
            return False

    def revert(self):
        """
        Revert stack and apply next unchecked partial coloring.
        :return:
        """
        colored = False
        while not colored:
            if len(self.colors_history) == 0:
                return False
            i_vtx, color, next_color = self.colors_history.pop(-1)
            if self.color_first_use[color] == i_vtx:
                self.color_first_use[color] = None
            self.unmark_neighbors(i_vtx, color)
            colored = self.color_vtx(i_vtx, next_color)
        return True

    def show(self, colors=None):
        G = nx.Graph()
        for vtx in self.vertices:
            for nbg in vtx.adj:
                G.add_edge(vtx.idx, nbg)

        pos = nx.spring_layout(G)
        if colors is None:
            colors = [self.n_colors if vtx.color is None else vtx.color for vtx in self.vertices]
        nx.draw(G, pos, with_labels=True, node_color=colors, edge_color='black', width=1,
                alpha=0.7)  # with_labels=true is to show the node number in the output graph
        plt.show()


# class SimpleColouring(Colouring):
#
#     def make_colouring(self, yield_every_iter=False):
#         """
#         Color next vtx.
#         :yield: Coloring if all vtxs are colored, None for other iter.
#         :return:  All colorings checked.
#         """
#         self.i_vtx = 0
#         while True:
#             if len(self.colors_history) == len(self.vertices):
#                 # all colored
#                 coloring = [vtx.color for vtx in self.vertices]
#                 self.n_colorings += 1
#                 #return Colouring.canonic_coloring(coloring)
#                 yield Colouring.canonic_coloring(coloring)
#                 if not self.revert():
#                    return
#             else:
#                 # partial coloring
#
#                 #print(self.i_vtx)
#                 n_used_colors = np.count_nonzero(self.neighbour_colors[self.i_vtx])
#                 if n_used_colors == self.n_colors:
#                     # Saturated vertex, we must backtrace
#                     if not self.revert():
#                         return
#                 else:
#                     self.color_vtx(self.i_vtx, 0)
#             if yield_every_iter:
#                yield None
#
#
#     def revert(self):
#         """
#         Revert stack and apply next unchecked partial coloring.
#         :return:
#         """
#         colored = False
#         while not colored:
#             if len(self.colors_history) == 0:
#                 return False
#             i_vtx, color, next_color = self.colors_history.pop(-1)
#             if self.color_first_use[color] == i_vtx:
#                 self.color_first_use[color] = None
#             self.unmark_neighbors(i_vtx, color)
#             colored = self.color_vtx(i_vtx, next_color)
#         return True


def write_coloring(out_stream, coloring):
    coloring = Colouring.canonic_coloring(coloring)
    for col in coloring:
        out_stream.write("%d\n"%(col))


def solve(in_stream, out_stream) :
    col = Colouring(in_stream)

    gen_coloring = col.make_colouring()
    coloring = next(gen_coloring)

    if type(coloring) == list:
        write_coloring(out_stream, coloring)
        return True
    else:
        return False

def permute(arr, old_to_new):
    new_arr = [0]*len(arr)
    for i_old in range(len(arr)):
        new_arr[old_to_new[i_old]] = arr[i_old]
    return new_arr



def make_data(in_stream, problem_size, s_factor=5):
    '''
    1. make teacher \times Blocks table
    2. Distribute subjects into the table
    3. Distribute students among  subjects selecting at most single subject per block
    4. Write down input and result.

    TODO:
    - produced graph is still to easy to color (no backtracking necessary)
    - try to have different subjects per block
    - remove teacher in first instance, distribute them as students after subjects are colored
    - possibly nearly clique graphs are easy to color
    '''
    import numpy as np
    np.random.seed(problem_size)

    n_subjs_pre_student = 0.5
    n_subjs = problem_size

    subj_permute = np.random.permutation(n_subjs)


    n_blocks = min(30, int(np.sqrt( n_subjs) *1.5))
    n_teachers = int( problem_size / n_blocks * 1.2)
    assert n_blocks * n_teachers >= n_subjs

    ns_per_st = int(n_subjs_pre_student* n_blocks)
    edges_per_student = ns_per_st * (ns_per_st - 1) / 2
    n_edges = n_subjs * (n_blocks - 1) * s_factor
    n_students = int(n_edges / edges_per_student)


    block_teacher_tab = (n_teachers*n_blocks)*[None]
    subj_teachers = []
    subj_blocks = []
    for i_subj in range(n_subjs):
        i_teacher = np.random.randint(0, n_teachers)
        i_block = np.random.randint(0, n_blocks)
        ii = i_block*n_teachers + i_teacher
        while block_teacher_tab[ii] is not None:
            ii += 1
            if ii  == len(block_teacher_tab):
                ii = 0
        block_teacher_tab[ii] = i_subj
        subj_teachers.append(int(ii%n_teachers))
        subj_blocks.append(int(ii/n_teachers))

    block_subjs = [ [] for i in range(n_blocks) ]
    for ii, subj in enumerate(block_teacher_tab):
        i_block = int(ii/n_teachers)
        if subj != None :
            block_subjs[i_block].append(subj)
    block_subjs = [ np.array(a) for a in block_subjs ]

    students = []
    blocks = np.arange(0, n_blocks)
    for st in range(n_students):
        #ns = max(1, min(n_blocks, int(random.gauss((n_blocks+1)*0.99,  n_blocks/12.0)) ))
        ns = int(n_blocks* n_subjs_pre_student)
        st_blocks = np.random.choice(blocks, size=ns, replace=False)
        st_subjs = []
        for bl in st_blocks:
            st_subjs.append(np.random.choice(block_subjs[bl]))
        #print(ns, st_blocks, st_subjs)
        students.append(st_subjs)

    in_stream = io.StringIO()
    res_stream = io.StringIO()
    # write input, permuted subjects
    in_stream.write("%d %d %d %d\n"%(n_students, n_subjs, n_teachers, n_blocks) )
    for st in students:
        for sj in st:
            in_stream.write("%d "%(subj_permute[sj]))
        in_stream.write("\n")
    for teacher in permute(subj_teachers, subj_permute):
        in_stream.write("%d\n"%(teacher))

    #sys.stdout.write(in_stream.getvalue())
    #print(subj_permute)

    # write output
    # write_coloring(res_stream, permute(subj_blocks, subj_permute))

    # Find all nontrivial colorings for given time interval.
    in_stream.seek(0)
    solve(in_stream, res_stream)
    # t = time.clock()
    # t_list = [t]
    # col = Colouring(in_stream)
    # #col = SimpleColouring(in_stream)
    # gen_coloring = col.make_colouring(yield_every_iter=False)
    # n_it = 0
    # for _ in gen_coloring:
    #     n_it += 1
    #     t = time.clock()
    #     if _ is not None:
    #         t_list.append(t)
    #     if t > t_list[0] + TIME_LIMIT:
    #         assert 0, "Outitmed."
    #         break
    #
    # t_list.append(time.clock())
    # # result = dict(seed=seed, n_vtx=n_subjs, n_colors=n_blocks, students_factor= float(n_students)/n_subjs,
    #      n_colorings=col.n_colorings, n_it=n_it, n_branching=col.n_branching,
    #      t_first=t_list[1] - t_list[0], t_all=t_list[-1]-t_list[0])
    # #print(json.dumps(result, sort_keys=True))
    #assert col.n_colorings == 1
    sys.stdout.write(in_stream.getvalue())






'''
Main script body.
'''
def main():
    parser = OptionParser()
    parser.add_option("-p", "--problem-size", type=int, dest="size", help="Problem size.", default=None)
    #parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None)
    parser.add_option("-r", dest="rand", action="store_true", help="Use rendomized seed. Otherwise problem size is used.")
    #parser.add_option("-f", dest="s_factor", type=float, default=0.4, help="Students per subject.")

    options, args = parser.parse_args()

    if options.rand:
        np.random.seed(rand)

    if options.size is not None:
        make_data(sys.stdout, options.size, s_factor = 7.5)
    else :
        # with open("in.0") as f_in:
        #     solve(f_in, sys.stdout)
        solve(sys.stdin, sys.stdout)

if __name__ == "__main__":
    main()
