# -*- coding: utf-8 -*-
"""

    create_flow_data.py

        Create a nodal flow file from spatial data

"""

#=======================
# Modules

import geopandas as gpd

# Add local directory to path
import sys
sys.path.append("../../")

# Import local functions
from utils import *

#=======================
# PROCESSING

def compute_supply_demand(nodes):
    '''Calculate demand based on population and ei
    '''
    nodes['flow'] = 0
    # supply
    # capacity (MW) * 10 ** 3 = kW
    nodes.loc[nodes.asset_type == 'source', 'flow'] = \
        nodes.loc[nodes.asset_type == 'source', 'capacity'] * 10 ** 6
    # demand
    # persons * kW/person = kW
    nodes.loc[nodes.asset_type == 'sink', 'flow'] = \
        nodes.loc[nodes.asset_type == 'sink', 'population'] * \
            nodes.loc[nodes.asset_type == 'sink', 'ei'] * 10 ** 3
    return nodes

# path_to_nodes = '../data/demo/nodes_demo.shp'
# path_to_edges = '../data/demo/edges_demo.shp'

path_to_nodes = '../data/spatial/infrasim-network/nodes.shp'
path_to_edges = '../data/spatial/infrasim-network/edges.shp'

# read data
network = read_data(path_to_nodes=path_to_nodes,
                    path_to_edges=path_to_edges)

print('loaded data')

# flow nodes
flow_nodes = get_flow_nodes(network).reset_index(drop=True)
flow_nodes = compute_supply_demand(flow_nodes)
flow_nodes['flow'] = flow_nodes['flow'] 

# pivot
flow_nodes = flow_nodes[['id','flow']]
list_of_nodes = flow_nodes.id.to_list()
flow_nodes = flow_nodes.pivot_table(columns='id').reset_index(drop=True)
flow_nodes['timestep'] = 1
flow_nodes = flow_nodes[['timestep'] + list_of_nodes]
flow_nodes = flow_nodes.astype('int64')

# save file
flow_nodes.to_csv('../data/csv/generated_nodal_flows.csv',index=False)

print('done')