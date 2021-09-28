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

def compute_demand(nodes):
    '''Calculate demand based on population and ei
    '''
    

# read data
network = read_data(path_to_nodes='../data/spatial/nodes_processed.shp')

# flow nodes
flow_nodes = get_flow_nodes(network).reset_index(drop=True)

flow_nodes['flow'] = 0

flow_nodes.loc[flow_nodes.asset_type == 'source', 'flow'] = \
    flow_nodes.loc[flow_nodes.asset_type == 'source', 'capacity'] * 1000

flow_nodes.loc[flow_nodes.asset_type == 'sink', 'flow'] = \
    flow_nodes.loc[flow_nodes.asset_type == 'sink', 'population'] * \
        flow_nodes.loc[flow_nodes.asset_type == 'sink', 'ei']



# # supplies
# supply_nodes = network.nodes.loc[network.nodes.asset_type == 'source'].reset_index(drop=True)

# supply_nodes = supply_nodes[['id','capacity']]

# # pivot
# t = supply_nodes.pivot_table(columns='id')