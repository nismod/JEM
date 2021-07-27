# -*- coding: utf-8 -*-
"""

    create_topology.py
    
        Script to process raw node and edge data. 
        
        Workflow:
            - Merge Multilinestrings from power line data       [Complete]
            - Add junction nodes where lines split              [Complete]
            - Add sink nodes to low voltage                     [TO DO]
            - Connect supply to substations                     [TO DO]
            - Create bi-directional high voltage grid           [TO DO]
            - Connect high voltage grid to low voltage grid     [TO DO]
            - Save processed spatial data                       [Complete]

"""


#=======================
# Modules

import geopandas as gpd
from shapely.geometry import Point
from shapely.wkt import loads
import re

# Add local directory to path
import sys
sys.path.append("../../")

# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *



#=======================
# FUNCTIONS

# Round coordinates
def coord_rounding(match):
    return "{:.5f}".format(float(match.group()))
simpledec = re.compile(r"\d*\.\d+")

# Merge edges in raw data
def jem_merge_edges(network):
    # add endpoints
    network = add_endpoints(network) 
    # add ids
    network = add_ids(network)
    # add topology
    network = add_topology(network, id_col='id')
    # merge using snkit
    network = merge_edges(network,by='Subtype')
    return network.edges



#=======================
# PRE-PROCESSING

# File paths
path_to_edges = '../data/demo/edges_demo.shp'
path_to_nodes = '../data/demo/nodes_demo.shp'

# Read edges and nodes
edges = gpd.read_file(path_to_edges)
nodes = gpd.read_file(path_to_nodes)

#---
# Edges pre-processing

# get edges representing HV system
edges_hv = edges

# explode multipart linestrings
edges_hv = edges_hv.explode()

#---
# Nodes pre-processing

# delete NoneTypes
nodes = nodes[~nodes.geometry.isna()].reset_index(drop=True)



#=======================
# PROCESSING

# Define network
network = Network(nodes,edges_hv)

# Merge edges in raw data
network.edges = jem_merge_edges(network)

# merge multilinestrings
network.edges.geometry = network.edges.geometry.apply(merge_multilinestring)

# [!!!]
# remove any remaining multilinestrings
network.edges = network.edges.loc[network.edges.geom_type != 'MultiLineString'].reset_index(drop=True)

# add endpoints
network = add_endpoints(network) 

# split edges between nodes
network = split_edges_at_nodes(network)

# add ids
network = add_ids(network)

# Save
network.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo_processed.shp')
network.edges.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo_processed.shp')








# #----
# # 1.1: Add junctions where lines split

# network = snkit.network.add_endpoints(network)

# # Round geom before dropping duplicates
# network.nodes.geometry = network.nodes.geometry.apply(lambda x: loads(re.sub(simpledec, coord_rounding, x.wkt)))
# # Drop duplicates
# network.nodes = snkit.network.drop_duplicate_geometries(network.nodes)

# # Add metadata
# network.nodes.loc[network.nodes.Type.isna(),'Type'] = 'junction'
# network.nodes.loc[network.nodes.Reference.isna(),'Reference'] = 'snkit'