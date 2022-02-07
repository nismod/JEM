# run_node_impact_assessment.py

This script is used to run a single-point failure analysis on the electricity nodal dataset. The process involves 'attacking' nodes one at a time and simulating the operations in the energy network, and then evaluating the sink nodes impacted. The files are setup to be run on the [ARC](https://www.arc.ox.ac.uk) linux server. Due to the computational expense of the process, the code is setup to be run in batch on 20 nodes (see below).

### How to run
Download/clone JEM repository and upload onto ARC workspace.

Configure parameters for the model run. Specifically, you'll need to set the following parameters:

- max_iterations 
- number_of_nodes

The first is related to the number of single failures you want to run. For example, if you have 43,200 assets to fail, then set this parameter to 45,000k (round it up to make the batching segments tidier). The next is the number of nodes you want to run the computation over. You'll need to adjust these parameters within ```run_node_impact_assessment.py``` and ```run_edge_impact_assessment.py```
