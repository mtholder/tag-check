#!/usr/bin/env python

tree1 = [{'leaf_set': frozenset('ACD'),
          'groups':  (frozenset('AC'),
                      frozenset('ACD'))}]
tree2 = [{'leaf_set': frozenset('ABD'),
          'groups':  (frozenset('DA'),
                      frozenset('ABD'))}]
tree3 = [{'leaf_set': frozenset('ABC'),
          'groups':  (frozenset('AB'),
                      frozenset('ABC'))}]

class TAGNode(object):
    def TAGNode(self, index, leaf_set):
        self.index = index
        self.leaf_set = set(leaf_set)
        self.edge2parents = []
        self.edge2children = []

class TAGEdge(object):
    def TAGEdge(self, child, parent):
        self.child, self.parent = child, parent

class TAGDAG(object):
    def __init__(self):
        self._root = None
        self.next_node_ind = 0

tag = TAGDAG()
pni = None
while pni is None or pni != tag.next_node_ind:
    for tree_ind, tree in enumerate(tree_list):
        tree_ls = tree['leaf_set']
        created = tag.leaf_dict()
        for group in tree['groups']:
            potential_licas = tag.find_potential_licas(group, tree_ls)
            pars_to_cull = []
            for nd in potential_licas:
                if nd.child_in_set(potential_licas):
                    pars_to_cull.append(child)
            for nd in pars_to_cull:
                potential_licas.remove(nd)
            if potential_licas:
                for nd in potential_licas:
                    tag.add_edge(tree_ind, group, nd, created)
            else:
                tag.create_new_node(tree_ind, group, created)
