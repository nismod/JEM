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


def assign_pop_to_sinks(network,epsg=3448,
                        node_id_column='id',population_id_column='population'):
    '''Assign population to sink nodes
    '''
    # get sinks
    nodes_dataframe = network.nodes[network.nodes['asset_type'] == 'sink']
    # get parish boundaries
    parish_boundaries = gpd.read_file('../data/spatial/else/admin-boundaries.shp')
    # get population dataframe
    population_dataframe = gpd.read_file('../data/population-russell/population.gpkg')

    # rename
    nodes_dataframe['parish'] = nodes_dataframe['parish'].str.replace('Kingston','KSA')
    nodes_dataframe['parish'] = nodes_dataframe['parish'].str.replace('St. Andrew','KSA')
    parish_boundaries['Parish'] = parish_boundaries['Parish'].str.replace('KSA','KSA')
    parish_boundaries['Parish'] = parish_boundaries['Parish'].str.replace('St','St.')

    # change crs
    nodes_dataframe = nodes_dataframe.to_crs(epsg=epsg)
    parish_boundaries = parish_boundaries.to_crs(epsg=epsg)
    population_dataframe = population_dataframe.to_crs(epsg=epsg)

    # compute
    new_nodes = assign_node_weights_by_population_proximity(nodes_dataframe=nodes_dataframe,
                                                            parish_boundaries=parish_boundaries,
                                                            population_dataframe=population_dataframe,
                                                            node_id_column=node_id_column,
                                                            population_id_column=population_id_column,
                                                            epsg=epsg
                                                            )
    #remap
    pop_mapped = new_nodes[['id','population']].set_index('id')['population'].to_dict()
    # reassign
    network.nodes['population'] = network.nodes['id'].map(pop_mapped).fillna(0)
    return network
