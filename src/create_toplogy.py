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
from tqdm import tqdm
tqdm.pandas()

# Add local directory to path
import sys
sys.path.append("../../")

# Import infrasim spatial tools
from JEM.infrasim.spatial import get_isolated_graphs

# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *

# Import local functions
from utils import *
from merge_cost_data import *
from electricity_demand_assignment import *

#=======================
# GLOBAL PARAMS

remove_connected_components = False
connected_component_tolerance = 15


#=======================
# PROCESSING

# read data
network = read_data()
verbose_print('loaded data')

# remove known bugs
if 'bug' in network.edges.columns:
    network.edges = network.edges[network.edges.bug != 'true'].reset_index(drop=True)
verbose_print('removed known bugs')

# merge multilinestrings
network = remove_multiline(network)
verbose_print('removed multilines')

# delete NoneType
network = remove_nontype(network)
verbose_print('removed NonType')

# explode multipart linestrings
network = explode_multipart(network)
verbose_print('explode multipart linestrings')

# save raw data from jps
jps_nodes = network.nodes.copy()
jps_edges = network.edges.copy()

# Merge edges
network = add_endpoints(network)
verbose_print('added end points')

# add ids
network = add_ids(network)
verbose_print('added IDs')

# add topology
network = add_topology(network, id_col='id')
verbose_print('added topology')

# merge using snkit
# network = merge_edges(network,by='asset_type')
verbose_print('merged edges')

# remove multilines again...
network = remove_multiline(network)

#===
# SNAP LV LINES TO SUBSTATIONS

verbose_print('snapping lines to substations...')

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

verbose_print('done')



#===
# ADD JUNCTIONS AND SINKS

verbose_print('adding junctions and sinks...')

# add endpoints
network = add_endpoints(network)
# update asset_type
network.nodes.loc[~network.nodes.subtype.isin(['sink','junction','sink']),'subtype'] = 'pole'
network.nodes.loc[~network.nodes.asset_type.isin(['sink','junction','sink']),'asset_type'] = 'junction'
# split edges between nodes
network = split_edges_at_nodes(network)
# add ids
network = update_notation(network)
## network.edges.drop(['id','from_id','to_id'],axis=1)
## network = add_id_to_nodes(network)
## network = add_edge_notation(network)
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

verbose_print('done')



#===
# CONVERT FALSE JUNCTIONS TO SINKS

verbose_print('converting false junctions...')

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

verbose_print('done')



#===
# CLEANING/FORMATTING

# add length to line data
network = add_edge_length(network)
verbose_print('added line lengths')

# remove duplicated
network = remove_duplicates(network)
verbose_print('removed duplicates')

# add max/min
network = add_limits_to_edges(network)
verbose_print('added limits to edge flows')

# double-up edges
network = bidirectional_edges(network)
verbose_print('made edges bidirectional')

# remove sink-to-sink connections
network = remove_sink_to_sink(network)
verbose_print('removed sink to sinks')

# add node degree
network = add_nodal_degree(network)
verbose_print('added nodal degrees')

# drop zero degree sinks
network = remove_stranded_nodes(network)
verbose_print('removed stranded nodes')

# remove self-loops
network = remove_self_loops(network)
verbose_print('removed self-loops')

# change asset_type of sinks with >2 degree connectivity
network.nodes.loc[(network.nodes.degree > 2) & \
                  (network.nodes.asset_type == 'sink'), 'asset_type'] = 'junction'

verbose_print('converted sinks of degree>0 to junctions')



#===
# ADD COST DATA
verbose_print('merging cost data...')

network = merge_cost_data(network,
                        path_to_costs='../data/costs_and_damages/maximum_damage_values.csv',
                        print_to_console=False)

verbose_print('done')



#===
# ADD POPULATION
verbose_print('adding population...')
population = gpd.read_file('../data/incoming_data/admin_boundaries.gpkg',layer='admin3')
network = assign_pop_to_sinks(network,population)
verbose_print('done')


#===
# GET CONNECTED COMPONENTS
verbose_print('getting connected components...')

network = add_component_ids(network)
# remove
if not remove_connected_components:
    pass
else:
    graphs_to_remove = network.edges.loc[network.edges.nx_part > connected_component_tolerance]
    nodes_to_remove = graphs_to_remove.from_id.to_list() + graphs_to_remove.to_id.to_list()
    edges_to_remove = graphs_to_remove.id.to_list()
    # drop
    network.nodes = network.nodes.loc[~network.nodes.id.isin(nodes_to_remove)].reset_index(drop=True)
    network.edges = network.edges.loc[~network.edges.id.isin(edges_to_remove)].reset_index(drop=True)
# Update network notation
network = update_notation(network)

verbose_print('done')



#===
# REINDEX
network.edges = network.edges[['id', 'asset_type', 'from_id', 'to_id', 'from_type', 'to_type',
                               'voltage', 'losses', 'length', 'min', 'max', 'cost_min',
                               'cost_max', 'cost_avg','cost_uom','name', 'parish',
                               'source', 'component_id', 'geometry']]

network.nodes = network.nodes[['id','asset_type','subtype','capacity',
                              'cost_min','cost_max','cost_avg','cost_uom',
                              'degree','parish','title','source','geometry']]

verbose_print('re-indexed data')

#===
# SAVE DATA
verbose_print('saving...')

save_data(network)

verbose_print('create_toplogy finished')
