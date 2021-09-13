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
            - Create bi-directional grid                        [Complete]
            - Save processed spatial data                       [Complete]

"""


#=======================
# Modules
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

## DEMO?
demo_run_type = False

#=======================
# FUNCTIONS

# Round coordinates
def coord_rounding(match):
    return "{:.5f}".format(float(match.group()))
simpledec = re.compile(r"\d*\.\d+")

# Merge edges in raw data
def jem_merge_edges(network):
    # add endpoints
    print('1...')
    network = add_endpoints(network) 
    # add ids
    print('2...')
    network = add_ids(network)
    # add topology
    print('3...')
    network = add_topology(network, id_col='id')
    # merge using snkit
    print('4...')
    #network = merge_edges(network,by='asset_type')
    return network.edges

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

#=======================
# PRE-PROCESSING

# File paths
if demo_run_type is True:
    path_to_edges = '../data/demo/edges_demo.shp'
    path_to_nodes = '../data/demo/nodes_demo.shp'
else:
    # Demo file paths
    path_to_edges = '../data/spatial/edges.shp'
    path_to_nodes = '../data/spatial/nodes.shp'

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


#=======================
# PROCESSING

# Define network
network = Network(nodes,edges)

# save jps nodes
jps_nodes = network.nodes.copy()

#===
# REMOVE MULTILINESTRINGS

# Merge edges in raw data
network.edges = jem_merge_edges(network)
print('> Merged edges in raw data')

# merge multilinestrings
network.edges.geometry = network.edges.geometry.apply(merge_multilinestring)
print('> Merged Multilinestrings')

# [!!! FIX THIS AT SOME POINT !!!]
# remove any remaining multilinestrings
network.edges = network.edges.loc[network.edges.geom_type != 'MultiLineString'].reset_index(drop=True)
print('> Removed remaining Multilinestrings')


#===
# SNAP LV LINES TO SUBSTATIONS

# LV
lv_voltages = ['24 kV', '12 kV']

# get substations
substations = network.nodes[network.nodes.subtype == 'substation'].geometry

# loop
for s in substations:
    # index edges
    idx_edges = edges_within(s,
                             network.edges[network.edges.voltage.isin(lv_voltages)],
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

# add endpoints
network = add_endpoints(network) 

# update asset_type
network.nodes.loc[~network.nodes.subtype.isin(['sink','junction','sink']),'subtype'] = 'pole'
network.nodes.loc[~network.nodes.asset_type.isin(['sink','junction','sink']),'asset_type'] = 'junction'

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
network.nodes.loc[network.nodes.id.isin(true_sinks),'asset_type'] = 'sink'
network.nodes.loc[network.nodes.id.isin(true_sinks),'subtype'] = 'demand'

# remap asset_type and asset_type from original data
for n in jps_nodes.title:
    network.nodes.loc[network.nodes.title == n, 'asset_type'] = jps_nodes.loc[jps_nodes.title == n].asset_type.iloc[0]
    network.nodes.loc[network.nodes.title == n, 'subtype'] = jps_nodes.loc[jps_nodes.title == n].subtype.iloc[0]

print('> Added junctions and sinks')



#===
# CONVERT FALSE JUNCTIONS TO SINKS 
nodes_to_test = network.nodes[network.nodes.subtype.isin(['pole'])].reset_index(drop=True)
for n in nodes_to_test.id:
#for n in ['node_1694']:
    degree = node_connectivity_degree(node=n, network=network)
    if degree == 1:
        # change node asset_type
        network.nodes.loc[network.nodes.id == n, 'asset_type'] = 'sink'
        network.nodes.loc[network.nodes.id == n, 'subtype'] = 'demand'
        # reverse arc direction
        prev_line = network.edges[network.edges.from_id == n].geometry.values[0]
        network.edges.loc[network.edges.from_id == n, 'geometry'] = flip(prev_line)



#===
# FORMATTING

# add length to line data
network.edges['length_km'] = network.edges.geometry.length * 10**-3



#===
# UPDATE NETWORK NOTATION
network = update_notation(network)



#===
# REMOVE DUPLICATED

network.edges = network.edges.drop_duplicates(subset=['from_id', 'to_id'], keep='first').reset_index(drop=True)



#===
# ADD MAX/MIN

network.edges['min'] = 0 
network.edges['max'] = 1.000000e+12



#===
# REDUCE SAMPLE

if demo_run_type is True:
    
    # get microsample attributes
    edges_attributes = gpd.read_file('../data/demo/edges_demo_microsample.shp')
    nodes_attributes = gpd.read_file('../data/demo/nodes_demo_microsample.shp')
    
    # copy
    edges_microsample = network.edges.copy()
    nodes_microsample = network.nodes.copy()
    
    # resample
    edges_microsample = edges_microsample.loc[edges_microsample.geometry.isin(edges_attributes.geometry)].reset_index(drop=True)
    nodes_microsample = nodes_microsample.loc[nodes_microsample.geometry.isin(nodes_attributes.geometry)].reset_index(drop=True)



#===
# DOUBLE-UP EDGES

def bidirectional_edges(edges):
    ''' Converts to edges bi-directional edges
    '''
    ee = edges.copy()
    # reverse ids
    ee['from_id']   = edges['to_id']
    ee['to_id']     = edges['from_id']
    # reverse geom
    for i in ee.index:
        ee.loc[i,'geometry'] = flip(ee.loc[i].geometry)
    # append
    edges = edges.append(ee,ignore_index=True)
    return edges

network.edges       = bidirectional_edges(network.edges)

if demo_run_type is True:
    edges_microsample   = bidirectional_edges(edges_microsample)

print('> Doubled up edges')

# Update network notation... again
# network = update_notation(network)



#===
# ADD EDGE FROM_TYPE,TO_TYPE

nodal_keys = network.nodes[['id','asset_type']].set_index('id')['asset_type'].to_dict()
network.edges['from_type']  = network.edges['from_id'].map(nodal_keys)
network.edges['to_type']    = network.edges['to_id'].map(nodal_keys)

print('> Added from_type,to_type notation to edges')


#===
# REMOVE ISLANDED ASSETS

# remove sink-to-sink connections
sink_to_sink = network.edges.loc[\
                    (network.edges.from_type == 'sink') & \
                        (network.edges.to_type== 'sink')].reset_index(drop=True)

nodes_to_remove = sink_to_sink.from_id.to_list() + sink_to_sink.to_id.to_list()
edges_to_remove = sink_to_sink.id.to_list() 

#network.nodes = network.nodes.loc[~network.nodes.id.isin(nodes_to_remove)].reset_index(drop=True)
network.edges = network.edges.loc[~network.edges.id.isin(edges_to_remove)].reset_index(drop=True)

# add node degree
network.nodes['degree'] = network.nodes.id.apply(lambda x: node_connectivity_degree(x,network=network))

# drop zero degree sinks
idx = network.nodes.loc[(network.nodes.degree == 0) & \
                        (network.nodes.asset_type == 'sink')].index

network.nodes = network.nodes.drop(idx).reset_index(drop=True)

# change asset_type of sinks with >2 degree connectivity
network.nodes.loc[(network.nodes.degree > 2) & \
                  (network.nodes.asset_type == 'sink'), 'asset_type'] = 'junction'

print('> Removed islanded assets')
    
    
#===
# ADJUST COLUMN ATTRIBUTES

#---
# edges: 
#   [asset_type,type,from_id,to_id,from_type,to_type,voltage,losses,length_km,min,max,name,parish,source]


# append cost_per_km

# reindex
network.edges = network.edges[['id','asset_type','from_id','to_id','from_type','to_type',\
                               'voltage','losses','length_km','min','max',\
                                   'name','parish','source','geometry']]

#---
# nodes:
#   [asset_type,type,subtype,capacity,unit_cost,cost_uom,degree,name,parish,source]


# reindex
network.nodes['unit_cost']  = 0
network.nodes['cost_uom']   = 'USD/MW'
network.nodes['name']      = network.nodes['title']

network.nodes = network.nodes[['id','asset_type','subtype','capacity',\
                                'unit_cost','cost_uom','degree',\
                                    'name','parish','source','geometry']]

# Update network notation... again
# network = update_notation(network)

print('> Adjusted column attributes')

    
#===
# ADD SUBGRAPH TAG AND REMOVE SMALL SUBGRAPHS

# tag
network.nodes,network.edges = get_isolated_graphs(network.nodes,network.edges)

# get small graphs
subgraph_tolerance = 1 #99999999
small_graphs = network.edges.loc[network.edges.nx_part > subgraph_tolerance]

# get index
nodes_to_remove = small_graphs.from_id.to_list() + small_graphs.to_id.to_list()
edges_to_remove = small_graphs.id.to_list() 

# drop
network.nodes = network.nodes.loc[~network.nodes.id.isin(nodes_to_remove)].reset_index(drop=True)
network.edges = network.edges.loc[~network.edges.id.isin(edges_to_remove)].reset_index(drop=True)

# Update network notation... again
network = update_notation(network)

print('> Removed small subgraphs with ' + str(subgraph_tolerance) + ' tolerance')


#===
# REMOVE SELF-LOOPS

network.edges = network.edges[network.edges.from_id != network.edges.to_id].reset_index(drop=True)

# Update network notation... again
network = update_notation(network)


#===
# SAVE DATA

if demo_run_type is True:
    # demo
    network.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo_processed.shp')
    network.edges.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo_processed.shp')
    # micrsample
    nodes_microsample.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_demo_microsample_processed.shp')
    edges_microsample.to_file(driver='ESRI Shapefile', filename='../data/demo/edges_demo_microsample_processed.shp')
else:
    network.nodes.to_file(driver='ESRI Shapefile', filename='../data/spatial/nodes_processed.shp')
    network.edges.to_file(driver='ESRI Shapefile', filename='../data/spatial/edges_processed.shp')


print('> Saved data to /data/demo/')


# #===
# # TEST DATA

# network.nodes = network.nodes.loc[(network.nodes.degree > 0) & \
#                                   (network.nodes.asset_type == 'sink')].reset_index(drop=True)


# network.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/nodes_test.shp')