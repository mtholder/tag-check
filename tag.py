#!/usr/bin/env python
import sys
MAX_NUM_PROCESSING_ROUNDS = 4

VERBOSE = -1
CRASHING = False
def debug_var(level, var_name, var):
    if VERBOSE < level:
        return
    if type(var) in [set, frozenset, list, tuple]:
        svar = type(var)([str(i) for i in var])
        var = svar
    m = 'tag.py DEBUG: {} = {}'.format(var_name, var)
    debug(level, m)
def debug(level, m):
    if VERBOSE < level:
        return
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
    def is_empty(self):
        return (self.bijects_to_leaf is None) and (not self.edge2children)
    def child_in_set(self, possible_child):
        debug_var(2, ' child_in_set possible_par', self)
        for edge in self.edge2children:
            debug_var(2, ' child_in_set    edge.child', edge.child)
            if edge.child in possible_child:
                return True
        return False
    def bijects2leaf_str(self):
        if self.bijects_to_leaf:
            return 'MAPS_TO_LEAF=' + str(self.bijects_to_leaf)
        return 'NOT A LEAF'
    def leaf_set_str(self):
        ls = [i for i in self.leaf_set]
        ls.sort()
        return ', '.join(ls)
    def __str__(self):
        c = ', '.join(['Node({n}) via Edge({e})'.format(e=i.index, n=i.parent.index) for i in self.edge2parents])
        if self.is_empty():
            fmt = 'Empty TAG Node({i:d} ls={{}}) {b}. CHILDOF= [{c}]. PARENTOF=[]'
            return fmt.format(i=self.index, b=self.bijects2leaf_str(), c=c)
        else:
            p = ', '.join(['Node({n}) via Edge({e})'.format(e=i.index, n=i.child.index) for i in self.edge2children])
            fmt = 'TAG Node({i:d} ls={{{l}}}) {b}. CHILDOF= [{c}]. PARENTOF=[{p}]'
            return fmt.format(i=self.index, b=self.bijects2leaf_str(), c=c, p=p, l=self.leaf_set_str())
    @property
    def leaf_set(self):
        global CRASHING
        if CRASHING:
            return ['UNAVAILABLE']
        ls = set()
        if self.edge2children:
            if self.bijects_to_leaf is not None:
                CRASHING = True
                debug_var(-100, 'leaf_set node: ', str(self))
                assert False
            for edge in self.edge2children:
                cls = edge.child.leaf_set
                ls.update(cls)
        else:
            if self.bijects_to_leaf is None:
                CRASHING = True
                debug_var(-100, 'leaf_set node: ', str(self))
                assert False
            ls.add(self.bijects_to_leaf)
        assert ls
        return frozenset(ls)
class TAGEdge(object):
    def __init__(self, child, parent, index, label):
        assert child is not parent
        if parent.bijects_to_leaf is not None:
            debug_var(-100, 'TAGEdge.__init__ parent', str(parent))
            debug_var(-100, 'TAGEdge.__init__ child', str(child))
            assert parent.bijects_to_leaf is None
        self.child, self.parent = child, parent
        self.index = index
        self.label = label
    def __str__(self):
        frag = 'Node({c:d} ls={{{cl}}}) --[via edge {e:d} from tree{l}]--> Node({p:d} ls={{{pl}}}) '
        return frag.format(c=self.child.index, 
                           p=self.parent.index,
                           e=self.index,
                           l=str(self.label),
                           cl=self.child.leaf_set_str(),
                           pl=self.parent.leaf_set_str())

class TAGDAG(object):
    def __init__(self, tree_list=None, del_edges_for_reproc=False):
        self._root = None
        self._next_node_ind = 0
        self._edge_index = 0
        self._leaf_set = set()
        self._nodes = []
        self.processing_round = -1
        if tree_list is not None:
            self.process_to_completion(tree_list)
        self.del_edges_for_reproc = del_edges_for_reproc
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
    @property
    def num_connected_nodes(self):
        nn = self.num_nodes
        empty_nodes = [i for i in self._nodes if i.is_empty()]
        return nn - len(empty_nodes)
    def leaf_set(self):
        return frozenset(self._leaf_set)
    def debug_print(self, level, out=None):
        if VERBOSE < level:
            return
        if out is None:
            out = sys.stderr
        out.write('TAG has {n:d} nodes ({c} connected):\n'.format(n=self.num_nodes, c=self.num_connected_nodes))
        empty_nodes = []
        for nd in self._nodes:
            if nd.is_empty():
                empty_nodes.append(nd)
                continue
            e2plist = list(nd.edge2parents)
            if e2plist:
                e2plist_str = ',\n    '.join([str(e) for e in e2plist])
                c = 'CHILDOF relationship(s):\n    {c}\n'.format(c=e2plist_str)
            else:
                c = 'Not a CHILDOF any node.\n'

            ls = [str(i) for i in nd.leaf_set]
            ls.sort()
            ls = ', '.join(ls)

            ndf = '  TAG Node({i:d} ls={{{l}}}) {b}. {c}'
            out.write(ndf.format(i=nd.index,
                                 b=nd.bijects2leaf_str(),
                                 l=ls,
                                 c=c))
        if empty_nodes:
            out.write('Empty nodes:\n')
            for nd in empty_nodes:
                out.write('    {}\n'.format(str(nd)))

    def find_potential_licas(self, group, tree_ls):
        input_ingroup = frozenset(group)
        assert input_ingroup
        input_outgroup = tree_ls - input_ingroup
        potential_lica_set = set()
        tag_leafset = self.leaf_set()
        for node in self._nodes:
            if node.is_empty():
                # EMPTY NODE!
                continue
            node_ingroup = node.leaf_set
            assert node_ingroup
            node_outgroup = tag_leafset - node_ingroup
            if (input_ingroup & node_ingroup) \
               and (not (input_ingroup & node_outgroup)) \
               and (not (node_ingroup & input_outgroup)):
                debug_var(2, 'Adding another potential node', str(node))
                debug_var(2, 'find_potential_licas node_ingroup', node_ingroup)
                debug_var(2, 'find_potential_licas node_outgroup', node_outgroup)
                debug_var(2, 'find_potential_licas input_ingroup', input_ingroup)
                debug_var(2, 'find_potential_licas input_outgroup', input_outgroup)
                potential_lica_set.add(node)
        return potential_lica_set

    def align_trees(self, tree_list, processing_round):
        self.processing_round = processing_round
        for tree_ind, tree in enumerate(tree_list):
            tree_ls = tree['leaf_set']
            tree_clades = tree['clades']
            self.align_tree(tree_ls, tree_clades, tree_ind, processing_round)

    def del_edges_for_tree(self, tree_ind):
        for node in self._nodes:
            to_del = [e for e in node.edge2parents if e.label == tree_ind]
            for td in to_del:
                node.edge2parents.remove(td)
            to_del = [e for e in node.edge2children if e.label == tree_ind]
            for td in to_del:
                node.edge2children.remove(td)
    def align_tree(self, tree_leaf_set, tree_clade_list, tree_ind, processing_round):
        leaf_names = [i for i in tree_leaf_set]
        leaf_names.sort() # not necessary, but makes the process easier to follow
        debug_var(2, 'leaf_names', leaf_names)
        leaf_node_groups = [(frozenset(i), frozenset()) for i in leaf_names]
        debug_var(2, 'leaf_node_groups', leaf_node_groups)
        tree_groups = tuple(leaf_node_groups + list(tree_clade_list))
        debug_var(2, 'tree_groups', tree_groups)
        debug(0, 'processing round = {p:d} tree_id = {t}'.format(p=processing_round, t=str(tree_ind)))
        if self.del_edges_for_reproc and processing_round > 0:
            self.del_edges_for_tree(tree_ind)
        tag_nodes_for_this_tree = {}
        for group_ind, group in enumerate(tree_groups):
            key_for_in_node = (processing_round, tree_ind, group_ind)
            clade_leaf_set = group[0]
            debug_var(1, 'group ID = ', str(key_for_in_node))
            debug_var(1, 'clade_leaf_set', clade_leaf_set)
            # find the set of child nodes in the TAG that correspond to the 
            #   children of this clade. Since we are going in postorder
            #   down this input tree, we should not get a KeyError from
            #   tag_nodes_for_this_tree if the input tree descriptions are valid
            clade_children_leaf_set_iterable = group[1]
            debug_var(2, 'clade_children_leaf_set_iterable', clade_children_leaf_set_iterable)
            children_TAG_node_set_list = []
            for clade_children_leaf_set in clade_children_leaf_set_iterable:
                #for each child in the input tree, whe should have mapped it to a set of TAG nodes
                possible_child_TAG_node_for_this_leaf_set = tag_nodes_for_this_tree[clade_children_leaf_set]
                child_TAG_node_for_this_leaf_set = possible_child_TAG_node_for_this_leaf_set
                debug_var(1, 'child_TAG_node_for_this_leaf_set', child_TAG_node_for_this_leaf_set)
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
            debug_var(1, 'aligned tag_node_set', tag_node_set)
            self.debug_print(1)
        if VERBOSE == 0:
            self.debug_print(0)

    def align_in_node(self, tree_leaf_set, clade_leaf_set, children_TAG_node_set_list, key_for_in_node, tree_ind):
        debug_var(2, 'align_in_node clade_leaf_set', clade_leaf_set)
        all_children_in_tag = set()
        for children_TAG_node_set in children_TAG_node_set_list:
            all_children_in_tag.update(children_TAG_node_set)
        all_children_in_tag = frozenset(all_children_in_tag)
        potential_licas = self.find_potential_licas(clade_leaf_set, tree_leaf_set)
        debug_var(2, 'unfiltered potential_licas', potential_licas)
        # we can't map a child to itself (no loops)
        children_to_cull = set()
        for nd in potential_licas:
            if nd in all_children_in_tag:
                children_to_cull.add(nd)
        potential_licas = potential_licas - children_to_cull
        debug_var(2, 'no loops potential_licas', potential_licas)
        
        # if the parent is a potential LICA ("map to the shallowest")
        pars_to_cull = set()
        for nd in potential_licas:
            if nd.child_in_set(potential_licas):
                pars_to_cull.add(nd)
        lica_nodes = potential_licas - pars_to_cull
        debug_var(2, 'lica_nodes', lica_nodes)
        
        # sanity check
        for nd in lica_nodes:
            assert nd is not None
        debug_var(2, 'align_in_node about to check for new node needed. lica_nodes', [str(i) for i in lica_nodes])
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
        self.num_connected_nodes_prev = self.num_connected_nodes
        self.num_nodes_prev = self.num_nodes
        while True:
            self.align_trees(tree_list, self.processing_round + 1)
            if self.stopping_criterion_triggered():
                return
            if self.processing_round + 1 > MAX_NUM_PROCESSING_ROUNDS:
                raise RuntimeError('MAX_NUM_PROCESSING_ROUNDS = {} exceeded'.format(MAX_NUM_PROCESSING_ROUNDS))

    def stopping_criterion_triggered(self):
        if self.del_edges_for_reproc:
            if self.num_connected_nodes == self.num_connected_nodes_prev:
                return True
            self.num_connected_nodes_prev = self.num_connected_nodes
            return False
        else:
            if self.num_nodes == self.num_nodes_prev:
                return True
            self.num_nodes_prev = self.num_nodes
            return False
        


if __name__ == '__main__':
    #leaf_set is a set of each leaf label
    # clades is a postorder listing of each clade
    # clade is a set of descendant leaves, and a set containing the leaf set of each child of the clade's root
    import os
    if 'VERBOSE' in os.environ:
        VERBOSE = int(os.environ['VERBOSE'])
    FIRST_CASE = 'FIRST_CASE' in os.environ
    DEL_EDGE_ON_REPROC = 'DEL_EDGE_ON_REPROC' in os.environ
    tree1 = {'leaf_set': frozenset('ACD'),
             'clades': ((frozenset('AC'), frozenset([frozenset('A'), frozenset('C')])),
                        (frozenset('ACD'), frozenset([frozenset('AC'), frozenset('D')]))), }
    tree2 = {'leaf_set': frozenset('ABD'),
             'clades': ((frozenset('DA'), frozenset([frozenset('A'), frozenset('D')])),
                        (frozenset('ABD'), frozenset([frozenset('DA'), frozenset('B')]))), }
    tree3 = {'leaf_set': frozenset('ABC'),
             'clades': ((frozenset('AB'), frozenset([frozenset('A'), frozenset('B')])),
                        (frozenset('ABC'), frozenset([frozenset('AB'), frozenset('C')]))), }
    debug(-50, 'VERBOSE={v:d} FIRST_CASE={f:b} DEL_EDGE_ON_REPROC={d:b}'.format(v=VERBOSE, f=FIRST_CASE, d=DEL_EDGE_ON_REPROC))
    try:
        tag = TAGDAG(del_edges_for_reproc=DEL_EDGE_ON_REPROC)
        if FIRST_CASE:
            tag.process_to_completion(tree_list=[tree1, tree2, tree3])
        else:
            tag.process_to_completion(tree_list=[tree1, tree3, tree2])
    except RuntimeError as x:
        sys.stderr.write('TAG on exit\n')
        tag.debug_print(-1)
        sys.stderr.write('ERROR: TAG did not stop growing!\n')
        sys.exit(x)
    tag.debug_print(-1, sys.stdout)
