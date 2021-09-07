# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 11:42:53 2021

@author: aqua
"""

import geopandas as gpd
from timeit import default_timer as timer

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.wkt import loads
import re

# Add local directory to path
import sys
sys.path.append("../../")

# Import infrasim spatial tools
from JEM.infrasim.spatial import get_isolated_graphs

# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *

# Add ID attribute to nodes
def add_id_to_nodes(network):
    ids = ['node_' + str(i+1) for i in range(len(network.nodes))]
    network.nodes['id'] = ids
    return network

def add_id_to_edges(network):
    ids = ['edge_' + str(i+1) for i in range(len(network.edges))]
    network.edges['id'] = ids
    return network

# Add i,j notation to edges
def add_edge_notation(network):
    i_field = 'from_id'
    j_field = 'to_id'
    id_attribute = 'id'
    #find nearest node to the START coordinates of the line -- and return the 'ID' attribute
    network.edges[i_field] = network.edges.geometry.apply(lambda geom: nearest(Point(geom.coords[0]), network.nodes)[id_attribute])
    #find nearest node to the END coordinates of the line -- and return the 'ID' attribute
    network.edges[j_field] = network.edges.geometry.apply(lambda geom: nearest(Point(geom.coords[-1]), network.nodes)[id_attribute])
    return network

# reverse arc direction
def flip(line):   
    return LineString(reversed(line.coords))


# update network notation
def update_notation(network):
    # drop existing
    network.edges.drop(['id','from_id','to_id'],axis=1)
    network.nodes.drop(['id'],axis=1)
    # update
    network = add_id_to_nodes(network)
    network = add_id_to_edges(network)
    network = add_edge_notation(network)
    return network

path_to_edges = '../data/demo/edges_demo.shp'
path_to_nodes = '../data/demo/nodes_demo.shp'

# Read edges and nodes
edges = gpd.read_file(path_to_edges)
nodes = gpd.read_file(path_to_nodes)

#---
# Edges pre-processing

# delete NoneType
edges = edges.loc[edges.is_valid].reset_index(drop=True)

# explode multipart linestrings
edges = edges.explode()

#---
# Nodes pre-processing

# delete NoneType
nodes = nodes[~nodes.geometry.isna()].reset_index(drop=True)

print('> Pre-processed node,edge data')

# Define network
network = Network(nodes,edges)
network = add_id_to_nodes(network)
network = add_edge_notation(network)

#=============================================================================

# (1) List comprehension

start = timer()
edges_as_list = [(edges.loc[i].from_id, \
                      edges.loc[i].to_id) \
                         for i in edges.index]
    
end = timer()
print('List comprehension: ' + str(end - start) + ' seconds') 

# (2) itertuples
start = timer()
edges_as_list = [(e.from_id,e.to_id) for e in edges.itertuples()]    
end = timer()
print('Itertuples: ' + str(end - start) + ' seconds') 

# (3) zip
start = timer()
edges_as_list = list(zip(edges['from_id'],edges['to_id']))
end = timer()
print('Zip: ' + str(end - start) + ' seconds') 