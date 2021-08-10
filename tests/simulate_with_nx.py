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

# add edges
edges_as_list = [(i,j,w) for i in edges.from_id for j in edges.to_id for w in edges.length_km]


G.add_weighted_edges_from(edges_as_list)


#------
# Shortest path setup