# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 15:05:53 2021

@author: aqua
"""

import pandas as pd
import geopandas as gpd
from tqdm import tqdm
tqdm.pandas()

import sys
sys.path.append('../jamaica-infrastructure')
from scripts.preprocess.preprocess_utils import assign_node_weights_by_population_proximity


def assign_pop_to_sinks(network,pop_bound,
                        epsg=3448,nodal_id='id',pop_id='TOTAL_POP'):
    '''Assign population to sink nodes
    '''
    # get sinks
    sinks = network.nodes[network.nodes['asset_type'] == 'sink']
    # change crs
    sinks = sinks.to_crs(epsg=epsg)
    pop_bound = pop_bound.to_crs(epsg=3448)
    # compute
    new_nodes = assign_node_weights_by_population_proximity(sinks,
                                                            pop_bound,
                                                            nodal_id,
                                                            pop_id,
                                                            epsg=epsg)
    #remap
    pop_mapped = new_nodes[['id','TOTAL_POP']].set_index('id')['TOTAL_POP'].to_dict()
    # reassign
    new_nodes['population'] = new_nodes['id'].map(pop_mapped).fillna(0)
    network.nodes = new_nodes
    return network
    




# #-----------------
# # Read data

# # Parishes
# parish = gpd.read_file('../data/incoming_data/admin_boundaries.gpkg',layer='admin1')

# # Population
# population = gpd.read_file('../data/incoming_data/admin_boundaries.gpkg',layer='admin3')

# # Electricity nodes
# nodes = gpd.read_file('../data/spatial/nodes_processed.shp')
# sinks = nodes[nodes['asset_type'] == 'sink']

# # identify id columns
# nodal_id = 'id'
# population_id = 'TOTAL_POP'

# # set crs
# sinks = sinks.to_crs(epsg=3448)
# population = population.to_crs(epsg=3448)

# # compute
# new_nodes = assign_node_weights_by_population_proximity(sinks,
#                                                         population,
#                                                         nodal_id,
#                                                         population_id,
#                                                         epsg=3448)


# pop_mapped = new_nodes[['id','TOTAL_POP']].set_index('id')['TOTAL_POP'].to_dict()
