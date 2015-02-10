#!/usr/bin/env python
import sys
from tag import *
MAX_NUM_PROCESSING_ROUNDS = 4
VERBOSE = -1


if __name__ == '__main__':
    #leaf_set is a set of each leaf label
    # clades is a postorder listing of each clade
    # clade is a set of descendant leaves, and a set containing the leaf set of each child of the clade's root
    import os
    if 'VERBOSE' in os.environ:
        VERBOSE = int(os.environ['VERBOSE'])
    FIRST_CASE = 'FIRST_CASE' in os.environ
    ALIGNED_OUTGROUP_DEF = 'ALIGNED_OUTGROUP_DEF' in os.environ
    INFINITE_LOOP = 'INFINITE_LOOP' in os.environ
    del_edges_for_reproc = 'DEL_EDGE_ON_REPROC' in os.environ
    tree0 = {'leaf_set': frozenset('ABCDE'),
             'clades': ((frozenset('ABCDE'), frozenset([frozenset('A'),frozenset('B'),frozenset('C'),frozenset('D'),frozenset('E'),])),), }
    tree1 = {'leaf_set': frozenset('ACDE'),
             'clades': ((frozenset('AC'), frozenset([frozenset('A'), frozenset('C')])),
                        (frozenset('ACD'), frozenset([frozenset('AC'), frozenset('D')])), 
                        (frozenset('ACDE'), frozenset([frozenset('ACD'), frozenset('E')]))), }
    tree2 = {'leaf_set': frozenset('ABDE'),
             'clades': ((frozenset('DA'), frozenset([frozenset('A'), frozenset('D')])),
                        (frozenset('ABD'), frozenset([frozenset('DA'), frozenset('B')])), 
                        (frozenset('ABDE'), frozenset([frozenset('ABD'), frozenset('E')]))),  }
    tree3 = {'leaf_set': frozenset('ABCE'),
             'clades': ((frozenset('AB'), frozenset([frozenset('A'), frozenset('B')])),
                        (frozenset('ABC'), frozenset([frozenset('AB'), frozenset('C')])), 
                        (frozenset('ABCE'), frozenset([frozenset('ABC'), frozenset('E')]))),  }
    debug(-50, 'VERBOSE={v:d} FIRST_CASE={f:b} DEL_EDGE_ON_REPROC={d:b}'.format(v=VERBOSE, f=FIRST_CASE, d=del_edges_for_reproc))
    if FIRST_CASE:
        tree_list = [tree0, tree1, tree2, tree3]
    else:
        tree_list = [tree0, tree1, tree3, tree2]
    main(tree_list, 
         del_edges_for_reproc,
         subset_of_aligned_outgroup_def=ALIGNED_OUTGROUP_DEF,
         infinite_loop=INFINITE_LOOP)