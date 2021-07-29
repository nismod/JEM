# -*- coding: utf-8 -*-
"""

    create_topology.py
    
        Script to process raw node and edge data. 
        
        Workflow:
            - Merge Multilinestrings from power line data       [Complete]
            - Add junction nodes where lines split              [Complete]
            - Add sink nodes to low voltage                     [Complete]
            - Connect supply to substations                     [Complete]
            - Connect high voltage grid to low voltage grid     [Complete]
            - Create bi-directional grid                        [TO DO]
            - Save processed spatial data                       [Complete]

"""


#=======================
# Modules
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

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

# Add ID attribute to nodes
def add_id_to_nodes(network):
    ids = ['node_' + str(i+1) for i in range(len(network.nodes))]
    network.nodes['id'] = ids
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



#===
# REMOVE MULTILINESTRINGS

# Merge edges in raw data
network.edges = jem_merge_edges(network)

# merge multilinestrings
network.edges.geometry = network.edges.geometry.apply(merge_multilinestring)

# [!!!]
# remove any remaining multilinestrings
network.edges = network.edges.loc[network.edges.geom_type != 'MultiLineString'].reset_index(drop=True)

print('> Removed Multilinestrings')



#===
# SNAP LV LINES TO SUBSTATIONS

# LV
lv_voltages = ['24 kV', '12 kV']

# get substations
substations = network.nodes[network.nodes.Subtype == 'substation'].geometry

# loop
for s in substations:
    # index edges
    idx_edges = edges_within(s,
                             network.edges[network.edges.VOLTAGE.isin(lv_voltages)],
                             distance=40)
    # snap
    for e in idx_edges.itertuples():
        # get current coords of edge
        e_coords = list(e.geometry.coords)
        # get coords of point
        s_coords = list(s.coords)
        # modify first coord of edge to be coord of point (i.e. snap)
        e_coords[0] = s_coords[0]
        # update in edge data
        network.edges.loc[network.edges.index == e.Index, 'geometry'] = LineString(e_coords)
        
print('> Updated coords')


    
#===
# ADD JUNCTIONS AND SINKS

# save jps nodes
jps_nodes = network.nodes.copy()

# add endpoints
network = add_endpoints(network) 

# update Type
network.nodes.loc[~network.nodes.Type.isin(['sink','junction','sink']),'Subtype'] = 'pole'
network.nodes.loc[~network.nodes.Type.isin(['sink','junction','sink']),'Type'] = 'junction'

# split edges between nodes
network = split_edges_at_nodes(network)

# add ids
network.edges.drop(['id','from_id','to_id'],axis=1)
network = add_id_to_nodes(network)
network = add_edge_notation(network)

# find true sink nodes
sinks = list(network.edges.to_id.unique())
starts = list(network.edges.from_id.unique())
true_sinks = []
for s in sinks:
    if s in starts:
        continue
    else:
        true_sinks.append(s)

# update true sinks
network.nodes.loc[network.nodes.id.isin(true_sinks),'Type'] = 'sink'
network.nodes.loc[network.nodes.id.isin(true_sinks),'Subtype'] = 'demand'

# remap Type and Subtype from original data
for n in jps_nodes.Name:
    network.nodes.loc[network.nodes.Name == n, 'Type'] = jps_nodes.loc[jps_nodes.Name == n].Type.iloc[0]
    network.nodes.loc[network.nodes.Name == n, 'Subtype'] = jps_nodes.loc[jps_nodes.Name == n].Subtype.iloc[0]

print('> Added junctions and sinks')



#===
# CONVERT FALSE JUNCTIONS TO SINKS 
nodes_to_test = network.nodes[network.nodes.Subtype.isin(['pole'])].reset_index(drop=True)
for n in nodes_to_test.id:
    degree = node_connectivity_degree(node=n, network=network)
    if degree == 1:
        # change node type
        network.nodes.loc[network.nodes.id == n, 'Subtype'] = 'demand'
        # reverse arc direction
        prev_line = network.edges[network.edges.from_id == n].geometry.values[0]
        network.edges.loc[network.edges.from_id == n, 'geometry'] = flip(prev_line)



#===
# FORMATTING

# add length to line data
network.edges['LengthKM'] = network.edges.geometry.length * 10**-3



#===
# SAVE DATA

network.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo_processed.shp')
network.edges.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo_processed.shp')

print('> Saved data to /data/demo/')