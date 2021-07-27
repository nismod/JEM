# -*- coding: utf-8 -*-
"""
Created on Fri May 28 10:16:24 2021

@author: hert5230
"""

import geopandas as gpd
from shapely.geometry import Point
from shapely.wkt import loads
import re

import sys
sys.path.append("../../")

from JEM.snkit.snkit.src.snkit.network import *

#-----------------------------------------------------------------------------
# WORKFLOW
#   
#   1. Create bi-directional high voltage grid
#
#       1.1 Add junctions where lines split
#       1.2 Connect generation sites (sources) to transmission substations (junctions)
#       1.3 Duplicate transmission system to capture bi-directionality
#       1.4 Post-processing and saving
#
#   2. Partition network by parishes
#
#-----------------------------------------------------------------------------


#=======================
# FUNCTIONS

def coord_rounding(match):
    return "{:.5f}".format(float(match.group()))

simpledec = re.compile(r"\d*\.\d+")

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
edges_hv = edges#[edges.Subtype.isin(['High Voltage'])].reset_index(drop=True)
# explode multipart linestrings
edges_hv = edges_hv.explode()

#---
# Nodes pre-processing

# delete NoneTypes
nodes = nodes[~nodes.geometry.isna()].reset_index(drop=True)

#=====================================================================
# PROCESSING
#=====================================================================

# Define network
network = Network(nodes,edges_hv)

# Merge edges
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

# #----
# # 1.2: Connect generation sites (sources) to transmission substations (junctions)


# #----
# # 1.3: Add sink at the end of each distribution line







# #----
# # 1.4 Post-processing and saving

# # Add IDs
# network.nodes['ID'] = ['n' + str(i+1) for i in network.nodes.index]
# network.edges['ID'] = ['n' + str(i+1) for i in range(len(network.edges.index))]











# # get edges representing HV system
# edges_hv = edges[edges.Subtype.isin(['High Voltage'])].reset_index(drop=True)



# # add IDs
# edges_hv['ID'] = ['a' + str(i+1) for i in edges_hv.index]
# nodes['ID'] = ['n' + str(i+1) for i in nodes.index]

# edges_hv['i'] = edges_hv.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[0]), nodes)['ID'])












# def add_graph_topology(nodes,edges,id_attribute='ID',save=False,label=False):
#     '''
#     Function to add i,j,k notation to edges
#     '''
#     i_field = 'i'
#     j_field = 'j'
#     #find nearest node to the START coordinates of the line -- and return the 'ID' attribute
#     edges[i_field] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[0]), nodes)[id_attribute])
#     #find nearest node to the END coordinates of the line -- and return the 'ID' attribute
#     edges[j_field] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[-1]), nodes)[id_attribute])
#     #order columns
#     # edges = edges[ metainfo['edges_header'] + ['geometry'] ]
#     #label
#     if label==True:
#         edges['label'] = '(' + edges[i_field] + ',' + edges[j_field] + ')'
#     #save
#     if save==True:
#         edges.to_file(driver='ESRI Shapefile', filename='edges_processed.shp')
#     return edges

# #edges_processed = add_graph_topology(nodes,edges,id_attribute='ID',save=False,label=False)