# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 10:35:48 2021

    Adding capacity attributes to version 1.0   
    
@amanmajid
"""

import sys
sys.path.append('../')

from src.utils import *
from infrasim.utils import *

from tqdm import tqdm
tqdm.pandas()


#----
# function
def nodal_capacity_from_edges(node,network):
    nodal_edges = get_nodal_edges(network,node).id.to_list()
    return network.edges.loc[network.edges.id.isin(nodal_edges)]['max'].max()


#----
# define input files
path_to_nodes = '../data/processed_data/version_1.0/nodes.shp'
path_to_edges = '../data/processed_data/version_1.0/edges.shp'

# read data
network = read_data(path_to_edges=path_to_edges,
                    path_to_nodes=path_to_nodes)

# drop fid
network.nodes = network.nodes.drop('fid',axis=1)
network.edges = network.edges.drop('fid',axis=1)

# adjust voltage
network.edges['voltage_kV'] = network.edges.voltage.str.replace('kV','').astype('int')

# calculate edge capacity
network = add_limits_to_edges(network)

# loop
network.nodes['capacity'] \
    = network.nodes.progress_apply(
        lambda x: nodal_capacity_from_edges(x['id'],network) \
            if pd.isnull(x['capacity']) else x['capacity'], axis=1 )

# remove capacities at demand nodes
network.nodes.loc[network.nodes.asset_type=='sink','capacity'] = np.nan

# save
save_data(network,
          path_to_edges=path_to_edges,
          path_to_nodes=path_to_nodes)