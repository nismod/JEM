# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 12:21:25 2021

@author: aqua
"""

import geopandas as gpd
from geopandas.tools import sjoin

path_to_raw     = '../data/spatial/edges.shp'
path_to_nodes   = '../data/spatial/nodes_processed.shp'
path_to_edges   = '../data/spatial/edges_processed.shp'


# Read edges and nodes
raw_edges   = gpd.read_file(path_to_raw)
edges       = gpd.read_file(path_to_edges)
nodes       = gpd.read_file(path_to_nodes)


# set crs
raw_edges.crs   = 'EPSG:3448'
edges.crs       = 'EPSG:3448'


# get buggy bits
raw_edges   = raw_edges.loc[raw_edges.bug == 'true'].reset_index(drop=True)
raw_edges   = raw_edges[['bug','geometry']]


# spatial join
joined_df = sjoin(edges, raw_edges, how="left")


# save
nodes.to_file(driver='ESRI Shapefile', filename='../_tmp/node_debugging.shp')
joined_df.to_file(driver='ESRI Shapefile', filename='../_tmp/edge_debugging.shp')