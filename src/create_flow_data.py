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
from merge_elec_consumption_data import *

#=======================
# PROCESSING

def compute_supply_demand(nodes):
    '''Calculate demand based on population and ei
    '''
    nodes['flow'] = 0
    # supply
    nodes.loc[nodes.asset_type == 'source', 'flow'] = \
        nodes.loc[nodes.asset_type == 'source', 'capacity']
    # demand
    nodes.loc[nodes.asset_type == 'sink', 'flow'] = \
        nodes.loc[nodes.asset_type == 'sink', 'population'] * \
            nodes.loc[nodes.asset_type == 'sink', 'ei']
    return nodes
    

# read data
network = read_data(path_to_nodes='../data/spatial/nodes_processed.shp')
print('loaded data')

# flow nodes
flow_nodes = get_flow_nodes(network).reset_index(drop=True)
flow_nodes = compute_supply_demand(flow_nodes)
flow_nodes['flow'] = flow_nodes['flow'] * 1000  # convert to kW