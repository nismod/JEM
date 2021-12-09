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
                                                            epsg=epsg,
                                                            save=True,
                                                            voronoi_path='../data/spatial/electricity_voronoi.shp',
                                                            )
    #remap
    pop_mapped = new_nodes[['id','TOTAL_POP']].set_index('id')['TOTAL_POP'].to_dict()
    # reassign
    network.nodes['population'] = network.nodes['id'].map(pop_mapped).fillna(0)
    return network
