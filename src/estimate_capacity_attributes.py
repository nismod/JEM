# -*- coding: utf-8 -*-
"""

    estimate_capacity_attributes.py
    
        Script to estimate the capacity of nodes/edges based on the simulated
            results of an steady-state ideal power network.
        
        ---
        Methodology description
        
        - The raw data does not have capacity attributes for nodes and edges. This
          is an issue given that we need capacity attributes for the damage-loss functions.
          
        - Our workaround is to setup a simulation of a steady-state idealised power network. 
          In other words, a network that is working perfectly without any damages.
         
        - Capacities can then be computed based on the results of the steady-state system.
    
    
@amanmajid
"""

import sys
sys.path.append('../')

from infrasim.model import *
from infrasim.utils import *

#------------------------------------
# RUN MODEL

# define input files
path_to_flows = '../data/csv/generated_nodal_flows.csv'
path_to_nodes = '../data/spatial/nodes_processed.shp'
path_to_edges = '../data/spatial/edges_processed.shp'

# init model
jem = infrasim(path_to_nodes,
               path_to_edges,
               path_to_flows,
               #timesteps=1,
               print_to_console=False,
               #nodes_to_attack=['node_25651'],
               #edges_to_attack=['edge_25297'],
               super_source=False,
               super_sink=False)

# build model
jem.build()

# run model
jem.run(print_to_console=True)

#------------------------------------
# GET RESULTS

def valuation_formula(node_id,edge_caps):
    # get edges around node
    idx_edge_id = get_nodal_edges(jem, node=node_id).id.to_list()
    # get maximum capacity
    return edge_caps.loc[edge_caps.id.isin(idx_edge_id)]['cap_estimate'].max()





edge_caps = estimate_edge_capacity(jem,rounding=False)
jem.edges['cap_est'] = edge_caps['cap_estimate']


jem.nodes['cap_estimate'] = jem.nodes.head(5).id.apply(lambda x: valuation_formula(x,edge_caps))






a = jem.edges
a.voltage_kV = a.voltage_kV.astype('int')
a = a.head(100)
a = a[['id','voltage_kV','cap_est']]
a['cap_est2'] = a.voltage_kV * 10**3 * 700 / 10**6