#!/usr/bin/env python
import sys
MAX_NUM_PROCESSING_ROUNDS = 2

VERBOSE = False
def debug_var(var_name, var):
    m = 'tag.py DEBUG: {} = {}'.format(var_name, var)
    sys.stderr.write(m)
    if not m.endswith('\n'):
        sys.stderr.write('\n')
class TAGNode(object):
    def __init__(self, index, name, leaf):
        self.index = index
        self.edge2parents = set()
        self.edge2children = set()
        self.bijects_to_leaf = leaf
        self.name = name
    def child_in_set(self, possible_child):
        for edge in self.edge2children:
            if edge.child is possible_child:
                return True
        return False
    def __str__(self):
        c = ', '.join(['Node({n}) via Edge({e})'.format(e=i.index, n=i.parent.index) for i in self.edge2parents])
        p = ', '.join(['Node({n}) via Edge({e})'.format(e=i.index, n=i.child.index) for i in self.edge2children])
        fmt = 'TAG Node({i:d}) bijects_to_leaf={b}. CHILDOF= [{c}]. PARENTOF=[{p}]\n'
        return fmt.format(i=self.index, b=str(self.bijects_to_leaf), c=c, p=p)
    @property
    def leaf_set(self):
        ls = set()
        if self.edge2children:
            if self.bijects_to_leaf is not None:
                debug_var('leaf_set node: ', str(self))
                assert self.bijects_to_leaf is None
            for edge in self.edge2children:
                cls = edge.child.leaf_set
                ls.update(cls)
        else:
            assert self.bijects_to_leaf is not None
            ls.add(self.bijects_to_leaf)
        assert ls
        return frozenset(ls)
class TAGEdge(object):
    def __init__(self, child, parent, index, label):
        assert child is not parent
        if parent.bijects_to_leaf is not None:
            debug_var('TAGEdge.__init__ parent', str(parent))
            debug_var('TAGEdge.__init__ child', str(child))
            assert parent.bijects_to_leaf is None
        self.child, self.parent = child, parent
        self.index = index
        self.label = label
    def __str__(self):
        frag = 'Node({c:d}) --[via edge {e:d} from tree{l}]--> Node({p:d}) '
        return frag.format(c=self.child.index, 
                           p=self.parent.index,
                           e=self.index,
                           l=str(self.label))

class TAGDAG(object):
    def __init__(self, tree_list=None):
        self._root = None
        self._next_node_ind = 0
        self._edge_index = 0
        self._leaf_set = set()
        self._nodes = []
        self.processing_round = -1
        if tree_list is not None:
            self.process_to_completion(tree_list)
    def create_new_node(self, key_for_in_node, bijects_to_leaf):
        if bijects_to_leaf is not None:
            self._leaf_set.add(bijects_to_leaf)
        nd = TAGNode(self.num_nodes, key_for_in_node, bijects_to_leaf)
        self._nodes.append(nd)
        return nd
    def add_edge(self, child, parent, label):
        assert child is not None
        assert parent is not None
        e = TAGEdge(child, parent, self._edge_index, label)
        self._edge_index += 1
        child.edge2parents.add(e)
        parent.edge2children.add(e)
        return e
    @property 
    def num_nodes(self):
        return len(self._nodes)
    def leaf_set(self):
        return frozenset(self._leaf_set)
    def debug_print(self):
        out = sys.stderr
        out.write('TAG has {n:d} nodes:\n'.format(n=self.num_nodes))
        for nd in self._nodes:
            e2plist = list(nd.edge2parents)
            if e2plist:
                e2plist_str = ',\n    '.join([str(e) for e in e2plist])
            else:
                e2plist_str = 'Child of no nodes.'
            ls = [str(i) for i in nd.leaf_set]
            ls.sort()
            ls = ', '.join(ls)
            ndf = '  TAG Node({i:d}) bijects_to_leaf={b}. leaf_set=[{l}]. CHILDOF relationship(s):\n    {c}\n'
            out.write(ndf.format(i=nd.index,
                                 b=str(nd.bijects_to_leaf),
                                 l=ls,
                                 c=e2plist_str))

    def find_potential_licas(self, group, tree_ls):
        input_ingroup = frozenset(group)
        assert input_ingroup
        input_outgroup = tree_ls - input_ingroup
        potential_lica_set = set()
        tag_leafset = self.leaf_set()
        for node in self._nodes:
            node_ingroup = node.leaf_set
            assert node_ingroup
            node_outgroup = tag_leafset - node_ingroup
            if (input_ingroup & node_ingroup) \
               and (not (input_ingroup & node_outgroup)) \
               and (not (node_ingroup & input_outgroup)):
                if VERBOSE:
                   debug_var('Adding another potential node', str(node))
                   debug_var('find_potential_licas node_ingroup', node_ingroup)
                   debug_var('find_potential_licas node_outgroup', node_outgroup)
                   debug_var('find_potential_licas input_ingroup', input_ingroup)
                   debug_var('find_potential_licas input_outgroup', input_outgroup)
                potential_lica_set.add(node)
        return potential_lica_set

    def align_trees(self, tree_list, processing_round):
        self.processing_round = processing_round
        for tree_ind, tree in enumerate(tree_list):
            tree_ls = tree['leaf_set']
            tree_clades = tree['clades']
            self.align_tree(tree_ls, tree_clades, tree_ind, processing_round)

    def align_tree(self, tree_leaf_set, tree_clade_list, tree_ind, processing_round):
        leaf_names = [i for i in tree_leaf_set]
        leaf_names.sort() # not necessary, but makes the process easier to follow
        if VERBOSE:
            debug_var('leaf_names', leaf_names)
        leaf_node_groups = [(frozenset(i), frozenset()) for i in leaf_names]
        if VERBOSE:
            debug_var('leaf_node_groups', leaf_node_groups)
        tree_groups = tuple(leaf_node_groups + list(tree_clade_list))
        if VERBOSE:
            debug_var('tree_groups', tree_groups)
        
        tag_nodes_for_this_tree = {}
        for group_ind, group in enumerate(tree_groups):
            key_for_in_node = (processing_round, tree_ind, group_ind)
            clade_leaf_set = group[0]
            if VERBOSE:
                debug_var('clade_leaf_set', clade_leaf_set)
            # find the set of child nodes in the TAG that correspond to the 
            #   children of this clade. Since we are going in postorder
            #   down this input tree, we should not get a KeyError from
            #   tag_nodes_for_this_tree if the input tree descriptions are valid
            clade_children_leaf_set_iterable = group[1]
            if VERBOSE:
                debug_var('clade_children_leaf_set_iterable', clade_children_leaf_set_iterable)
            children_TAG_node_set_list = []
            for clade_children_leaf_set in clade_children_leaf_set_iterable:
                #for each child in the input tree, whe should have mapped it to a set of TAG nodes
                child_TAG_node_for_this_leaf_set = tag_nodes_for_this_tree[clade_children_leaf_set]
                assert(len(child_TAG_node_for_this_leaf_set) > 0)
                children_TAG_node_set_list.append(child_TAG_node_for_this_leaf_set)
            # align the input node, making edges as needed
            tag_node_set = self.align_in_node(tree_leaf_set,
                                              clade_leaf_set,
                                              children_TAG_node_set_list,
                                              key_for_in_node, 
                                              tree_ind)
            # store the TAG nodes for this leaf set for this tree, they will be the
            #   child nodes in the next set of edges for this tree.
            tag_nodes_for_this_tree[clade_leaf_set] = tag_node_set
            self.debug_print()

    def align_in_node(self, tree_leaf_set, clade_leaf_set, children_TAG_node_set_list, key_for_in_node, tree_ind):
        if VERBOSE:
            debug_var('align_in_node clade_leaf_set', clade_leaf_set)
        all_children_in_tag = set()
        for children_TAG_node_set in children_TAG_node_set_list:
            all_children_in_tag.update(children_TAG_node_set)
        all_children_in_tag = frozenset(all_children_in_tag)
        potential_licas = self.find_potential_licas(clade_leaf_set, tree_leaf_set)
        # we can't map a child to itself (no loops)
        children_to_cull = set()
        for nd in potential_licas:
            if nd in all_children_in_tag:
                children_to_cull.add(nd)
        potential_licas = potential_licas - children_to_cull
        # if the parent is a potential LICA ("map to the shallowest")
        pars_to_cull = set()
        for nd in potential_licas:
            if nd.child_in_set(potential_licas):
                pars_to_cull.add(node)
        lica_nodes = potential_licas - pars_to_cull
        # sanity check
        for nd in lica_nodes:
            assert nd is not None
        if VERBOSE:
            debug_var('align_in_node about to check for new node needed. lica_nodes', [str(i) for i in lica_nodes])
        # add new node if needed
        if not lica_nodes:
            if len(clade_leaf_set) == 1:
                bijects_to_leaf = [i for i in clade_leaf_set][0]
            else:
                bijects_to_leaf = None
            lica_nodes = [self.create_new_node(key_for_in_node, bijects_to_leaf)]
            for nd in lica_nodes:
                assert nd is not None
        for child_TAG_node in all_children_in_tag:
            assert child_TAG_node is not None
            for par in lica_nodes:
                assert par is not None
                self.add_edge(child_TAG_node, par, tree_ind)
        return frozenset(lica_nodes)

    def process_to_completion(self, tree_list):
        num_nodes_prev = self.num_nodes
        while True:
            self.align_trees(tree_list, self.processing_round + 1)
            if num_nodes_prev == self.num_nodes:
                return
            if self.processing_round + 1 > MAX_NUM_PROCESSING_ROUNDS:
                raise RuntimeError('MAX_NUM_PROCESSING_ROUNDS = {} exceeded'.format(MAX_NUM_PROCESSING_ROUNDS))




if __name__ == '__main__':
    #leaf_set is a set of each leaf label
    # clades is a postorder listing of each clade
    # clade is a set of descendant leaves, and a set containing the leaf set of each child of the clade's root

    tree1 = {'leaf_set': frozenset('ACD'),
             'clades': ((frozenset('AC'), frozenset([frozenset('A'), frozenset('C')])),
                        (frozenset('ACD'), frozenset([frozenset('AC'), frozenset('D')]))), }
    tree2 = {'leaf_set': frozenset('ABD'),
             'clades': ((frozenset('DA'), frozenset([frozenset('A'), frozenset('D')])),
                        (frozenset('ABD'), frozenset([frozenset('DA'), frozenset('B')]))), }
    tree3 = {'leaf_set': frozenset('ABC'),
             'clades': ((frozenset('AB'), frozenset([frozenset('A'), frozenset('B')])),
                        (frozenset('ABC'), frozenset([frozenset('AB'), frozenset('C')]))), }
    tag = TAGDAG(tree_list=[tree1, tree2, tree3])
