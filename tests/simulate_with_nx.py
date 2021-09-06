# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 08:50:20 2021

@author: aqua
"""

import networkx as nx
import geopandas as gpd

nodes = gpd.read_file('../data/demo/nodes_demo_processed.shp')
edges = gpd.read_file('../data/demo/edges_demo_processed.shp')

#------
# Generate graph
#   - simple definition using i,j notation without attributes

# init graph
G = nx.Graph()

# add nodes
G.add_nodes_from(nodes.id.to_list())

# create list of weighted edges
edges_as_list = [(edges.loc[i].from_id, 
                  edges.loc[i].to_id, 
                  edges.loc[i].length_km) for i in edges.index]

# add edges to graph
G.add_weighted_edges_from(edges_as_list)

#------
# Get isolated subgraphs

# get connected_components
connected_parts = sorted(nx.connected_components(G), key = len, reverse=True)

# tag each individual network
count = 1
edges['nx_part'] = 0
for part in connected_parts:
    
    edges.loc[ (edges.from_id.isin(list(part))) | \
               (edges.to_id.isin(list(part))), 'nx_part' ] = count
        
    count = count + 1

nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo_processed.shp')
edges.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo_processed.shp')

#------
# Shortest path setup
#   TO DO 


