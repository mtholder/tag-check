# tag.py
A standalone python tool for building tree-alignment-graphs (sensu Smith, Brown, Hinchliff)

Not vetted at all. WARNING!

usage:

Input order should not affect the TAG.

So the results (sys.stdout) of running should be the same whether you are running
with FIRST_CASE in the env or not.

This runs the program in a mode where the edges of a tree are *not* removed before the tree is reprocessed
(and it terminates when the # of connected nodes in the graph stops changing):

    $ VERBOSE=0 FIRST_CASE=1 python tag.py >first-order-out.txt 2>first-order-err.txt
    $ VERBOSE=0 python tag.py >second-order-out.txt 2>second-order-err.txt


This runs the program in a mode where the edges of a tree *are* removed before the tree is reprocessed
(and it terminates when the # of nodes in the graph stops changing):

    $ VERBOSE=0 DEL_EDGE_ON_REPROC=1 FIRST_CASE=1 python tag.py >first-order-out.txt 2>first-order-err.txt
    $ VERBOSE=0 DEL_EDGE_ON_REPROC=1 python tag.py >second-order-out.txt 2>second-order-err.txt

At this point neither case generates a pair of isomorphic graphs. Which could be a bug in this script...


## TODO

  1. create diff-able summary of TAG to make it easier to check problem cases.
  2. create newick reader to generate the funky clade description format


## Acknowledgements
Thanks to Ruchi Chaudhary, Jonathan Rees, Stephen Smith, Joseph Brown, and Cody Hinchliff for discussions.