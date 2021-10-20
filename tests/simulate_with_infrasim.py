# -*- coding: utf-8 -*-
"""

    simulate_with_infrasim.py
    
        Script to carry out simulation with infrasim.
    
@amanmajid
"""

import sys
sys.path.append('../')

from jem.model import jem
from jem.analyse import analyse
from jem.utils import *

#------------------------------------
# RUN MODEL

# define input files
path_to_flows = '../data/csv/generated_nodal_flows.csv'
path_to_nodes = '../data/spatial/infrasim-network/version_1.0/nodes_component_1.shp'
path_to_edges = '../data/spatial/infrasim-network/version_1.0/edges_component_1.shp'

# init model
run = jem(path_to_nodes,
        path_to_edges,
        path_to_flows,
        #timesteps=1,
        print_to_console=False,
        nodes_to_attack=['node_23721'],
        #edges_to_attack=['edge_25297'],
        super_source=True,
        super_sink=False)

# build model
run.build()

# run model
run.optimise(print_to_console=True)

results = analyse(model_run=run)

print(results.supply_demand_balance())
print(results.nodes_with_shortfall())
print(results.customers_affected())


# def get_customers_affected(self):
#     return 'meow'