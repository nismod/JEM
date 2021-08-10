# -*- coding: utf-8 -*-
"""

    create_flow_data.py
    
        Script to produce supply and demand data. 
        
        Workflow:
            -
            -
            -
            -
            -

"""

#=======================
# Modules
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import geopandas as gpd
import random



#=======================
# READ DATA

# File paths
# path_to_edges = '../data/demo/edges_demo_microsample_processed.shp'
# path_to_nodes = '../data/demo/nodes_demo_microsample_processed.shp'

path_to_edges = '../data/demo/edges_demo_processed.shp'
path_to_nodes = '../data/demo/nodes_demo_processed.shp'

# Read edges and nodes
edges = gpd.read_file(path_to_edges)
nodes = gpd.read_file(path_to_nodes)



#=======================
# PRE-PROCESS

# get sources and sinks
asset_types = ['source','sink']

# index flow nodes
flow_nodes = nodes.loc[nodes.asset_type.isin(asset_types)].reset_index(drop=True)

# get columns of interest
flow_nodes = flow_nodes[['id']]

# add blank demand
flow_nodes['Demand'] = 1

# pivot
flow_nodes = flow_nodes.pivot(columns='id')

# unstack
flow_nodes.columns = flow_nodes.columns.droplevel()

# nodes
nodes_with_flow = flow_nodes.columns.to_list()

# add infrasim attributes
flow_nodes['timestep'] = flow_nodes.index + 1

# reorder columns
flow_nodes = flow_nodes[ ['timestep'] + nodes_with_flow ]

# sample a set number of timesteps
flow_nodes = flow_nodes[flow_nodes.timestep < 25].reset_index(drop=True)



#=======================
# CREATE DATA

supply_nodes = nodes.loc[nodes.asset_type.isin(['source']),'id'].to_list()
demand_nodes = nodes.loc[nodes.asset_type.isin(['sink']),'id'].to_list()

# supply
flow_nodes[supply_nodes] = 9999

# demand
for c in demand_nodes:
    #flow_nodes[c] = [random.random()*10 for i in range(0,len(flow_nodes))]
    flow_nodes[c] = [5 for i in range(0,len(flow_nodes))]



#=======================
# SAVE DATA

flow_nodes.to_csv('../data/demo/csv/nodal_flows.csv',index=False)