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
from JEM.jem.spatial import get_isolated_graphs
from JEM.jem.utils import get_nodal_edges

# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *

# Import local functions
from utils import *
from merge_cost_data import *
from electricity_demand_assignment import *
from merge_elec_consumption_data import *

#=======================
# GLOBAL PARAMS

verbose_flag=True
remove_connected_components = True
connected_component_tolerance = 99


#=======================
# PROCESSING

# read data
network = read_data()
verbose_print('loaded data',flag=verbose_flag)

# remove known bugs
if 'bug' in network.edges.columns:
    network.edges = network.edges[network.edges.bug != 'true'].reset_index(drop=True)
verbose_print('removed known bugs',flag=verbose_flag)

# merge multilinestrings
network = remove_multiline(network)
verbose_print('removed multilines',flag=verbose_flag)

# delete NoneType
network = remove_nontype(network)
verbose_print('removed NonType',flag=verbose_flag)

# explode multipart linestrings
network = explode_multipart(network)
verbose_print('explode multipart linestrings',flag=verbose_flag)

# save raw data from jps
jps_nodes = network.nodes.copy()
jps_edges = network.edges.copy()

# Merge edges
network = add_endpoints(network)
verbose_print('added end points',flag=verbose_flag)

# add ids
network = add_ids(network)
verbose_print('added IDs',flag=verbose_flag)

# add topology
network = add_topology(network, id_col='id')
verbose_print('added topology',flag=verbose_flag)

# merge using snkit
# network = merge_edges(network,by='asset_type')
verbose_print('merged edges',flag=verbose_flag)

# remove multilines again...
network = remove_multiline(network)

#===
# SNAP LV LINES TO SUBSTATIONS

verbose_print('snapping lines to substations...',flag=verbose_flag)

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

verbose_print('done',flag=verbose_flag)



#===
# ADD JUNCTIONS AND SINKS

verbose_print('adding junctions and sinks...',flag=verbose_flag)

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

verbose_print('done',flag=verbose_flag)



#===
# CONVERT FALSE JUNCTIONS TO SINKS

verbose_print('converting false junctions...',flag=verbose_flag)

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

verbose_print('done',flag=verbose_flag)



#===
# CLEANING/FORMATTING

# add length to line data
network = add_edge_length(network)
verbose_print('added line lengths',flag=verbose_flag)

# remove duplicated
network = remove_duplicates(network)
verbose_print('removed duplicates',flag=verbose_flag)

# change voltage column format
network.edges['voltage_kV'] = network.edges.voltage.str.replace('kV','').astype('int')

# add max/min
network = add_limits_to_edges(network)
verbose_print('added limits to edge flows',flag=verbose_flag)

# double-up edges
network = bidirectional_edges(network)
verbose_print('made edges bidirectional',flag=verbose_flag)

# remove sink-to-sink connections
network = remove_sink_to_sink(network)
verbose_print('removed sink to sinks',flag=verbose_flag)

# add node degree
network = add_nodal_degree(network)
verbose_print('added nodal degrees',flag=verbose_flag)

# drop zero degree sinks
network = remove_stranded_nodes(network)
verbose_print('removed stranded nodes',flag=verbose_flag)

# remove self-loops
network = remove_self_loops(network)
verbose_print('removed self-loops',flag=verbose_flag)

# change asset_type of sinks with >2 degree connectivity
network.nodes.loc[(network.nodes.degree > 2) & \
                  (network.nodes.asset_type == 'sink'), 'asset_type'] = 'junction'

verbose_print('converted sinks of degree>0 to junctions',flag=verbose_flag)


#===
# ADD COST DATA
verbose_print('merging cost data...',flag=verbose_flag)

network = merge_cost_data(network,
                        path_to_costs='../data/costs_and_damages/maximum_damage_values.csv',
                        print_to_console=False)

verbose_print('done',flag=verbose_flag)


#===
# GET CONNECTED COMPONENTS
verbose_print('getting connected components...',flag=verbose_flag)

network = add_component_ids(network)
# remove
if not remove_connected_components:
    pass
else:
    graphs_to_remove = network.edges.loc[network.edges.component_id > connected_component_tolerance]
    nodes_to_remove = graphs_to_remove.from_id.to_list() + graphs_to_remove.to_id.to_list()
    edges_to_remove = graphs_to_remove.id.to_list()
    # drop
    network.nodes = network.nodes.loc[~network.nodes.id.isin(nodes_to_remove)].reset_index(drop=True)
    network.edges = network.edges.loc[~network.edges.id.isin(edges_to_remove)].reset_index(drop=True)
# Update network notation
network = update_notation(network)

verbose_print('done',flag=verbose_flag)


#===
# ADD CAPACITY ATTRIBUTES
verbose_print('adding capacity attributes to nodes...',flag=verbose_flag)

def nodal_capacity_from_edges(node,network):
    nodal_edges = get_nodal_edges(network,node).id.to_list()
    return network.edges.loc[network.edges.id.isin(nodal_edges)]['max'].max()


network.nodes['capacity'] \
    = network.nodes.progress_apply(
        lambda x: nodal_capacity_from_edges(x['id'],network) \
            if pd.isnull(x['capacity']) else x['capacity'], axis=1 )

verbose_print('done',flag=verbose_flag)


# #===
# # MAP ELEC ASSETS TO WATER ASSETS
# verbose_print('mapping water assets...',flag=verbose_flag)
# water_nodes = gpd.read_file('../data/water/merged_water_assets.shp')
# map_elec_and_water_assets(network.nodes,water_nodes)
# verbose_print('done',flag=verbose_flag)


#===
# ADD TOTAL COSTS

# edges
network.edges['cost_min'] = network.edges['uc_min'] * network.edges['max'] * network.edges['length']
network.edges['cost_max'] = network.edges['uc_max'] * network.edges['max'] * network.edges['length']
network.edges['cost_avg'] = network.edges['uc_avg'] * network.edges['max'] * network.edges['length']
network.edges['cost_uom'] = '$US'

# nodes
network.nodes['cost_min'] = network.nodes['uc_min'] * network.nodes['capacity']
network.nodes['cost_max'] = network.nodes['uc_max'] * network.nodes['capacity']
network.nodes['cost_avg'] = network.nodes['uc_avg'] * network.nodes['capacity']
network.nodes['cost_uom'] = '$US'


#===
# REINDEX
network.edges = network.edges[['id', 'asset_type', 'from_id', 'to_id', 'from_type', 'to_type',
                               'voltage_kV', 'losses', 'length', 'min', 'max', 
                               'uc_min','uc_max', 'uc_avg','uc_uom',
                               'cost_min','cost_max', 'cost_avg','cost_uom',
                               'name', 'parish','source', 'component_id', 'geometry']]

network.nodes = network.nodes[['id','asset_type','subtype','capacity',#'population','ei', 'ei_uom',
                              'uc_min','uc_max','uc_avg','uc_uom',
                              'cost_min','cost_max', 'cost_avg','cost_uom',
                              'degree','parish','title','source','geometry']]

verbose_print('re-indexed data',flag=verbose_flag)


#===
# SAVE DATA
verbose_print('saving...',flag=verbose_flag)

save_data(network)

verbose_print('create_toplogy finished',flag=verbose_flag)


# #===
# # ADD POPULATION
# verbose_print('adding population...',flag=verbose_flag)
# network = assign_pop_to_sinks(network)
# verbose_print('done',flag=verbose_flag)


# #===
# # APPEND ELECTRICITY INTENSITIES
# network = append_electricity_intensities(network)
# verbose_print('appended electricity data',flag=verbose_flag)