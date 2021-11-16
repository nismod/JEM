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

# Import local copy of snkit
from JEM.snkit.snkit.src.snkit.network import *

#=======================
# Scripting

def update_cost(df,costs,asset_type,index_col='subtype'):
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


def merge_cost_data(network,
                    path_to_costs='../data/costs_and_damages/maximum_damage_values.csv',
                    print_to_console=False):
    '''Merge costs with node/edge data
    '''
    costs = pd.read_csv(path_to_costs)
    #---
    # nodes
    network.nodes['cost_min'] = 0
    network.nodes['cost_max'] = 0
    network.nodes['cost_avg'] = 0
    network.nodes['cost_uom'] = ''
    # fix
    for n in ['solar','gas','wind','hydro','diesel','substation','pole','demand']:
        new_nodes = update_cost(network.nodes,costs,asset_type=n)
    # print result
    if print_to_console is True:
        print(new_nodes.groupby(by='subtype').max()['cost_min'])
    #---
    # edges
    network.edges['cost_min'] = 0
    network.edges['cost_max'] = 0
    network.edges['cost_avg'] = 0
    network.edges['cost_uom'] = ''
    # fix
    for a in ['low','high']:
        new_edges = update_cost(network.edges,costs,asset_type=a,index_col='asset_type')
    # update
    network.nodes = new_nodes
    network.edges = new_edges
    return network
