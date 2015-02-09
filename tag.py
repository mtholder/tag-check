#!/usr/bin/env python
MAX_NUM_PROCESSING_ROUNDS = 10
class TAGNode(object):
    def TAGNode(self, index, leaf_set):
        self.index = index
        self.leaf_set = set(leaf_set)
        self.edge2parents = []
        self.edge2children = []
    def child_in_set(self, possible_child):
        for edge in self.edge2children:
            if self.child is possible_child:
                return True
        return False

class TAGEdge(object):
    def TAGEdge(self, child, parent):
        self.child, self.parent = child, parent

class TAGDAG(object):
    def __init__(self, tree_list=None):
        self._root = None
        self._next_node_ind = 0
        self._leaf_set = set()
        self._nodes = []
        self.processing_round = -1
        if tree_list is not None:
            self.process_to_completion(tree_list)
    def leaf_set(self):
        return frozenset(self._leaf_set)
    def find_potential_licas(self, group, tree_ls):
        input_ingroup = frozenset(group)
        input_outgropu = tree_ls - input_ingroup
        potential_lica_set = set()
        tag_leafset = self.leaf_set()
        for node in self._nodes:
            node_ingroup = node.leaf_set
            node_outgroup = tag_leafset - node_ingroup
            if (input_ingroup & node_ingroup) \
               and (not (input_ingroup & node_outgroup)) \
               and (not (output_ingroup & node_ingroup)):
               potential_lica_set.add(node)
        return potential_lica_set

    def align_trees(self, tree_list, processing_round):
        self.processing_round = processing_round
        for tree_ind, tree in enumerate(tree_list):
            tree_ls = tree['leaf_set']
            tree_clades = tree['clades']
            align_tree(self, tree_ls, tree_clades, processing_round)
    def align_tree(self, tree_leaf_set, tree_clade_list, processing_round):
        leaf_names = [i for i in tree_ls]
        leaf_names.sort() # not necessary, but makes the process easier to follow
        leaf_node_groups = [(frozenset(i), frozenset()) for i in leaf_names]
        tree_groups = leaf_node_groups + tree_clades
        tag_nodes_for_this_tree = {}
        for group_ind, group in enumerate(tree_clade_list):
            key_for_in_node = (processing_round, tree_ind, group_ind)
            clade_leaf_set = group[0]
            # find the set of child nodes in the TAG that correspond to the 
            #   children of this clade. Since we are going in postorder
            #   down this input tree, we should not get a KeyError from
            #   tag_nodes_for_this_tree if the input tree descriptions are valid
            clade_children_leaf_set_iterable = group[1]
            children_TAG_node_set_list = []
            for clade_children_leaf_set in clade_children_leaf_set_iterable:
                #for each child in the input tree, whe should have mapped it to a set of TAG nodes
                child_TAG_node_for_this_leaf_set = tag_nodes_for_this_tree[clade_children_leaf_set]
                assert(len(child_TAG_node_for_this_leaf_set) > 0)
                children_TAG_node_set_list.append(child_TAG_node_for_this_leaf_set)
            # align the input node, making edges as needed
            tag_node_set = align_in_node(tree_leaf_set,
                                         clade_leaf_set,
                                         children_TAG_node_set_list,
                                         key_for_in_node)
            # store the TAG nodes for this leaf set for this tree, they will be the
            #   child nodes in the next set of edges for this tree.
            tag_nodes_for_this_tree[clade_leaf_set] = ns

    def align_in_node(self, tree_leaf_set, clade_leaf_set, children_TAG_node_set_list, key_for_in_node):
        potential_licas = tag.find_potential_licas(clade_leaf_set, tree_ls)
        pars_to_cull = []
        for nd in potential_licas:
            if nd.child_in_set(potential_licas):
                pars_to_cull.append(node)
        lica_nodes = [nd for nd in potential_licas if nd not in pars_to_cull]
        if not lica_nodes:
            lica_nodes = [tag.create_new_node(key_for_in_node)]
        for child_TAG_node_set in children_TAG_node_set_list:
            for child_TAG_node in child_TAG_node_set:
                tag.add_edge(child_TAG_node, nd, tree_ind)
        return frozenset(lica_nodes)

    def process_to_completion(self, tree_list):
        num_nodes_prev = self.get_num_nodes()
        while True:
            align_trees(tree_list, self.processing_round + 1)
            if num_nodes_prev == self.get_num_nodes():
                return
            if self.processing_round > MAX_NUM_PROCESSING_ROUNDS:
                raise RuntimeError('MAX_NUM_PROCESSING_ROUNDS = {} exceeded'.format(MAX_NUM_PROCESSING_ROUNDS))




if __name__ == '__main__':
    #leaf_set is a set of each leaf label
    # clades is a postorder listing of each clade
    # clade is a set of descendant leaves, and a set containing the leaf set of each child of the clade's root

    tree1 = {'leaf_set': frozenset('ACD'),
             'clades': ((frozenset('AC'), frozenset('AC')),
                        (frozenset('ACD'), frozenset(['AC', 'D']))), }
    tree2 = {'leaf_set': frozenset('ABD'),
             'clades': ((frozenset('DA'), frozenset('AD')),
                        (frozenset('ABD'), frozenset(['DA', 'B']))), }
    tree3 = {'leaf_set': frozenset('ABC'),
             'clades': ((frozenset('AB'), frozenset('AB')),
                        (frozenset('ABC'), frozenset(['AB', 'C']))), }
    tag = TAGDAG(tree_list=[tree1, tree2, tree3])
