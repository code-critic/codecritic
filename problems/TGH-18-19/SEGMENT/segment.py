#!/usr/bin/env python
from __future__ import print_function

from optparse import OptionParser
from random import randint
import random
import sys
import StringIO
import math


def image_from_stream(in_stream):
    image = Image( int(in_stream.next()) )     
    for row in in_stream:
        for int_token in row.split():
            image.image.append(int(int_token))
    assert len(image.image) == image.img_side * image.img_side
    return image


class Image:
    def __init__(self, size) :
        self.image=[]
        self.img_side = size
    
    def fill(self, num):
        self.image=self.img_side * self.img_side * [num]
    
    def pidx(self,i_row,i_col):
        return i_row*self.img_side + i_col

    def image_to_stream(self, stream, head=True):
        if head:
            stream.write( "{:d}\n".format(( self.img_side )) )
        for row in range(self.img_side):
            for col in range(self.img_side):
                stream.write( "{} ".format(( self.image[self.pidx(row,col)]) ))
            stream.write("\n")
            
    def neighbours(self, ii):
        N=self.img_side
        ngh_list = [ii - 1, ii + 1, ii - N, ii + N]
        if ii / N == 0:            ngh_list[2] = -1  # top
        if ii / N == N - 1:   ngh_list[3] = -1  # bottom
        if ii % N == 0:            ngh_list[0] = -1  # left
        if ii % N == N - 1:   ngh_list[1] = -1  # right
        return filter(lambda item: item != -1, ngh_list)

    def _fill_line(self, A, B, inc):
        """
        Correlated random line (vertiacl or horizontal), assume points A an B
        are filled
        :param A: start index in image
        :param B: end index in image
        :param inc: increment of index
        :return:
        """

        if B == A + inc:
            return
        else:
            #print("A: {},{} B:{}, {}".format(A / self.img_side, A % self.img_side, B / self.img_side, B % self.img_side))
            dist = (B-A)/inc
            AC_dist = (dist/2)
            BC_dist = dist - AC_dist
            C = A + AC_dist*inc
            A_val = self.image[A]
            B_val = self.image[B]
            scale = 0.5 * self.max_diff * 0.5 * dist * math.pow(float(dist)/self.img_side, 0.3)
            C_value=int(( A_val +  B_val) / 2.0  + scale * random.uniform(-1, 1))
            #C_value = int((A_val + B_val) / 2.0 )
            # guarantee that difference is not larger then 'max_diff'
            """
            if A_val > B_val:
                A_val, B_val = B_val, A_val
            # B is biger
            C_max = A_val + int(self.max_diff * AC_dist *0.5)
            C_min = B_val - int(self.max_diff * BC_dist*0.5)
            C_value = min( C_max, C_value, self.max)
            C_value = max( C_min, C_value, self.min)
            #print("Av: {} Cv: {} Bv:{} {} {} {}".format(A_val, C_value, B_val, self.max_diff, AC_dist, BC_dist))
            """
            self.image[C] = C_value
            self._fill_line(A,C,inc)
            self._fill_line(C, B, inc)

    def _fill_h_line(self, A, B):
        self._fill_line(self.pidx(A[0],A[1]), self.pidx(B[0],B[1]), 1)

    def _fill_v_line(self, A, B):
        self._fill_line(self.pidx(A[0], A[1]), self.pidx(B[0], B[1]), self.img_side)

    def _fill_h_split(self, A, B):
        ar, ac = A
        br, bc = B
        if (ar + 1 == br): return
        cr = (ar+br)/2
        self._fill_h_line( (cr, ac), (cr, bc))
        #self.plot()
        self._fill_v_split( A, (cr,bc))
        self._fill_v_split( (cr, ac), B)

    def _fill_v_split(self, A, B):
        ar, ac = A
        br, bc = B
        if (ac + 1 == bc): return
        cc = (ac+bc)/2
        self._fill_v_line( (ar, cc), (br, cc) )
        #self.plot()
        self._fill_h_split( A, (br,cc))
        self._fill_h_split( (ar, cc), B)

    def smooth(self):
        for i in range(len(self.image)):
            ngh_vals = [ self.image[n] for n in self.neighbours(i) ]
            ngh_vals.append(self.image[i])
            self.image[i] = sum(ngh_vals) / len(ngh_vals)

    def fill_random(self, max_diff):
        """
        Fill image with corellated random values in range 0:1024, with given maximal
        difference between neighbouring values.
        :param n:
        :return: range of values
        """

        self.min=0
        self.abs_max=2048
        self.max_diff=max_diff -1
        self.max = min(self.abs_max, self.max_diff * self.img_side / 4)

        self.fill(0)
        N= self.img_side -1
        # corners
        self.image[self.pidx(0, 0)] = random.randint(self.min, self.max)
        self.image[self.pidx(0, N)] = random.randint(self.min, self.max)
        self.image[self.pidx(N, 0)] = random.randint(self.min, self.max)
        self.image[self.pidx(N, N)] = random.randint(self.min, self.max)
        # horizontal border
        self._fill_h_line( (0, 0), (0, N))
        self._fill_h_line( (N, 0), (N, N))
        # vertical border
        self._fill_v_line( (0, 0), (N, 0))
        self._fill_v_line( (0, N), (N, N))
        # fill interior    
        self._fill_v_split( (0,0), (N,N) )

        # scale
        img_max = max(self.image)
        img_min = min(self.image)
        self.image = [  int(self.max*float((v-img_min))/(img_max - img_min))  for v in self.image]

        def is_diff_satisfied():
            for i in range(len(self.image)):
                for j in self.neighbours(i):
                    if abs(self.image[i] - self.image[j]) > max_diff:
                        #print("diff: ", abs(self.image[i] - self.image[j]) )
                        return False
            return True

        # smooth
        for n_smooth in range(10):
            #print(n_smooth)
            if is_diff_satisfied(): break
            self.smooth()
        assert(n_smooth < 10)

        # check max diff
        for i in range(len(self.image)):
            if self.image[i] > self.max or  self.image[i] < self.min:
                print("max, min: ", self.image[i], self.max, self.min)

    def plot(self):
        import numpy as np
        import matplotlib.pyplot as plt

        img = np.array(self.image).reshape((self.img_side, self.img_side))
        plt.imshow(img, interpolation="nearest")
        plt.show()

    def scale_value(self, row, col, range):
        idx = self.pidx(row,col)
        self.image[idx] = int(range[0] + (float(self.image[idx])/self.max) * (range[1] - range[0]))


# global variables
class SegmentImage :
    
    def __init__(self, image) :
        self.nodes = []

        self.image_size = image.img_side
        n_nodes = self.image_size * self.image_size
        edge_classes = [ [] for i in range(0,256) ]
        
        for idx, intensity in enumerate(image.image):
            #print "node: ", intensity, idx              
            self.nodes.append( [ intensity, idx, 0 ] )   # tuple: (intensity, component_idx, rank)
            # upper neighbour
            if ( idx/self.image_size > 0) :
                ngh = idx - self.image_size                  
                diff = abs( self.nodes[ngh][0] - self.nodes[idx][0])
                #print "edge: ", diff, ngh, idx
                edge_classes[diff].append( ( ngh, idx ) )
            # left neighbour
            if (idx%self.image_size > 0) :
                ngh = idx - 1
                diff = abs( self.nodes[ngh][0] - self.nodes[idx][0])
                #print "edge: ", diff, ngh, idx
                edge_classes[diff].append( ( ngh, idx ) ) 
        self.edges = sum(edge_classes, [])
        
        
        
    def find( self, node ):       
        # find root of component
        parent=node
        while( self.nodes[parent][1] != parent ) :
            parent = self.nodes[parent][1]
        root = parent
        
        # path compression
        parent=node
        while( self.nodes[parent][1] != parent ) :
            parent = self.nodes[parent][1]
            self.nodes[parent][1] = root
        return root    
    
    def union(self, comp_from, comp_to):
        # merge components
        if (self.nodes[comp_from][2] > self.nodes[comp_to][2]) :
            self.nodes[comp_to][1] = comp_from
        else :
            if (self.nodes[comp_from][2] < self.nodes[comp_to][2]) :
                self.nodes[comp_from][1] = comp_to
            else :
                self.nodes[comp_to][1] = comp_from
                self.nodes[comp_from][2] += 1

    
            
    def kruskal(self):
        n_nodes = len(self.nodes)
        n_edges =0 # number of edges in the forest
        for edge in self.edges:
            node_from = edge[0]
            node_to = edge[1]
            
            comp_from=self.find( self.nodes[node_from][1] )
            comp_to=self.find( self.nodes[node_to][1] )
                        
            if (comp_from != comp_to):
                self.union(comp_from, comp_to)
                #print "Edge: ", i_class, node_from, node_to, comp_from, comp_to    
                        
                #print "      new comps: ", find(node_from), find(node_to)
                # add edge
                n_edges += 1
                # stop before adding separating edge
                if (n_edges == n_nodes-2) :
                    #self.last_edge_class = i_class
                    self.last_edge = (node_from, node_to) 
                    return
                
    def check_uniqueness(self):
        # check that the last added edge was from different edge class
        # then the first next edge (separating edge)
        for i_class in range(0,255):
            if (len(edge_classes[i_class]) > 0 ):                
                break;
        if (i_class == self.last_edge_class):
            raise "Nonunique segmantation: {0} {1}".format(self.last_edge,edge_classes[i_class][0]) 


    def segmented_image(self):
        img = Image(self.image_size)
        back_comp = self.find( 0 )
        for row in range(0, self.image_size):
            for col in range(0,self.image_size):
                #print( "node: ", row*self.image_size+col, self.find( row*self.image_size+col), back_comp )
                if ( self.find( row*self.image_size+col) == back_comp ) :
                    img.image.append(0)
                else :
                    img.image.append(1)
        #img.image_to_stream(sys.stdout)
        return img
        






"""        
    
      
    # output reduced graph
    #graph.graph_output(in_stream)
    in_stream.write(image_stream.getvalue())
"""    


def solve(in_stream, out_stream) :
    img = image_from_stream(in_stream)
    si = SegmentImage(img)
    #si.read_image(in_stream)
    si.kruskal()
    si.segmented_image().image_to_stream(out_stream, head=False)


def make_data(in_stream, problem_size):
    '''
    1. Generate result segmented image.
        1. start with background on boarder, foreground elsewhere; put all background points into a list
        2. for every background pixel get a one foreground neighbour and swith it into background with 0.5 prob.
           remove points that have no foreground neighbours
        3. continue until half of points is in background
    2. get foreground and background color ranges
    3. fill background (breadth first search, color is average of neighbours +/- 1 at random)
    4. fill foreground
    '''

    # random texture in range 0, 1024
    img_side = problem_size
    fill_img = Image(problem_size)
    fill_img.fill_random(3)
    #fill_img.image_to_stream(sys.stdout)
    #fill_img.plot()


    # determine background and foreground ranges
    min_range_size = 2
    max_range_size = min(120, fill_img.max)

    fg_bg_dist = 6
    fg_size = randint(min_range_size, max_range_size)
    bg_size = randint(min_range_size, max_range_size)
    fg_min = randint(0, 256 - fg_size - bg_size - fg_bg_dist)
    bg_min = randint(fg_min + fg_bg_dist, 256 - fg_size - bg_size)
    fg_range = (fg_min, fg_min + fg_size)
    bg_range = (bg_min+ fg_size, bg_min+ fg_size + bg_size)

    if randint(0, 1) == 0:
        fg_range, bg_range = bg_range, fg_range

    # scale texture into ranges on sircle shape
    radius = randint(2, img_side / 3)
    x_center = randint(radius + 1, img_side - radius - 1)
    y_center = randint(radius + 1, img_side - radius - 1)

    def sqr(x):
        return x * x

    radius_2 = sqr(radius)
    segment = Image(img_side)
    segment.fill(0)
    for row in range(img_side):
        for col in range(img_side):
            if sqr(row - y_center) + sqr(col - x_center) < radius_2:
                # foreground
                segment.image[segment.pidx(row,col)] = 1
                fill_img.scale_value(row, col, fg_range)
            else:
                # background
                fill_img.scale_value(row, col, bg_range)
    #fill_img.plot()


    """
    # input for result image
    input_img = Image(img_side)
    input_img.fill(-2)

    def bfs_fill(image, segmented, idx, component, value_range):
        queue = [idx]
        while queue:
            node = queue.pop(0)
            ngh_vals = []
            for ngh in neighbours(node):
                if segmented.image[ngh] != component:
                    continue
                ngh_val = image.image[ngh]
                if ngh_val == -2:
                    queue.append(ngh)
                    image.image[ngh] = -1
                if ngh_val >= 0:
                    ngh_vals.append(ngh_val)
            if ngh_vals:
                value = sum(ngh_vals) / len(ngh_vals) + randint(-1, 1)
                value = max(min(value, value_range[1] - 1), value_range[0])
                max_diff = max([abs(val - value) for val in ngh_vals])
                assert (max_diff < fg_bg_dist - 2)
            else:
                value = randint(value_range[0], value_range[1] - 1)
            image.image[node] = value

    bfs_fill(input_img, res_img, bg_idx, 0, bg_range)
    bfs_fill(input_img, res_img, fg_idx, 1, fg_range)
    """

    # fill_img.image_to_stream(sys.stdout)
    # input_img.image_to_stream(sys.stdout)
    image_stream = StringIO.StringIO()
    fill_img.image_to_stream(image_stream)
    image_stream.seek(0)

    out_stream = StringIO.StringIO()
    solve(image_stream, out_stream)

    res_stream = StringIO.StringIO()
    segment.image_to_stream(res_stream, head=False)
    assert(out_stream.getvalue() == res_stream.getvalue())

    sys.stdout.write(image_stream.getvalue())

'''
Main script body.
'''

parser = OptionParser()
parser.add_option("-p", "--problem-size", dest="size", help="Problem size.", default=None)
parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None)
parser.add_option("-r", dest="rand", default=False, help="Use non-deterministic algo")

options, args = parser.parse_args()

#random.seed(1234)
random.seed()

if options.rand:
    random.seed(options.rand)

if options.size is not None:
    make_data(sys.stdout, int(options.size))
else :
    solve(sys.stdin, sys.stdout)
