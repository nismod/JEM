# -*- coding: utf-8 -*-
"""
Created on Fri Sep 10 16:01:11 2021

@author: aqua
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

#=======================
# Read data

# Read edges and nodes
edges = gpd.read_file('../data/spatial/edges_processed.shp')
nodes = gpd.read_file('../data/spatial/nodes_processed.shp')

# Read cost data
costs = pd.read_csv('../data/costs_and_damages/maximum_damage_values.csv')

#=======================
# Append

def update_cost(df,asset_type,index_col='subtype'):
    '''Update costs
    '''
    # lower
    df.loc[ \
        df[index_col].str.contains(asset_type,case=False),'cost_min'] \
            = int(costs.loc[ \
                costs.asset_type.str.contains(asset_type,case=False),\
                    'maximum_damage_lower'].iloc[0].replace(' ','').replace(',',''))
                
    # higher
    df.loc[ \
        df[index_col].str.contains(asset_type,case=False),'cost_max'] \
            = int(costs.loc[ \
                costs.asset_type.str.contains(asset_type,case=False),\
                    'maximum_damage_upper'].iloc[0].replace(' ','').replace(',',''))
    
    # average
    df.loc[ \
        df[index_col].str.contains(asset_type,case=False),'cost_avg'] \
            = int(costs.loc[ \
                costs.asset_type.str.contains(asset_type,case=False),\
                    'maximum_damage'].iloc[0].replace(' ','').replace(',',''))
    # units
    df.loc[ \
        df[index_col].str.contains(asset_type,case=False),'cost_uom'] \
            = costs.loc[ \
                costs.asset_type.str.contains(asset_type,case=False),\
                    'unit'].iloc[0]
                
    return df
    
# ------- 
# NODES

nodes['cost_min'] = 0
nodes['cost_max'] = 0
nodes['cost_avg'] = 0
nodes['cost_uom'] = ''

new_nodes = update_cost(nodes,asset_type='solar')
new_nodes = update_cost(nodes,asset_type='gas')
new_nodes = update_cost(nodes,asset_type='wind')
new_nodes = update_cost(nodes,asset_type='hydro')
new_nodes = update_cost(nodes,asset_type='diesel')
new_nodes = update_cost(nodes,asset_type='substation')
new_nodes = update_cost(nodes,asset_type='pole')

new_nodes = new_nodes[['id','asset_type','subtype','capacity',
                      'cost_min','cost_max','cost_avg','cost_uom',
                      'degree','parish','name','source','geometry']]

print(new_nodes.groupby(by='subtype').max()['cost_min'])

# ------- 
# EDGES

edges['cost_min'] = 0
edges['cost_max'] = 0
edges['cost_avg'] = 0
edges['cost_uom'] = ''

new_edges = update_cost(edges,asset_type='high',index_col='asset_type')
new_edges = update_cost(edges,asset_type='low',index_col='asset_type')

new_edges = new_edges[['id', 'asset_type', 'from_id', 'to_id', 'from_type', 'to_type',
                       'voltage', 'losses', 'length_km', 'min', 'max', 'cost_min',
                       'cost_max', 'cost_avg','cost_uom','name', 'parish',
                       'source', 'nx_part', 'geometry']]


# ------- 
# SAVE

nodes.to_file(driver='ESRI Shapefile', filename='../data/spatial/nodes_processed.shp')
edges.to_file(driver='ESRI Shapefile', filename='../data/spatial/edges_processed.shp')