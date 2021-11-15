# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 12:16:17 2021

@author: aqua
"""

import pandas as pd
import os
from tqdm import tqdm

import sys
sys.path.append('../')

from jem.model import jem
from jem.analyse import analyse
from jem.utils import *

#--------------------------------------------
# Get damaged nodes

node_path = '../data/risk-results/direct_damages/electricity_network_v1.0_nodes/'

collected = []
for f in tqdm(os.listdir(node_path)):
    if 'csv' in f:
        data = pd.read_csv(node_path + f, usecols=['id','hazard'])
        collected.append(data)
        

collected = pd.concat(collected,ignore_index=True)
nodes_damaged = collected.id.unique()

#--------------------------------------------
# Simulate damages in loop

# define input files
path_to_flows = '../data/csv/generated_nodal_flows.csv'
path_to_nodes = '../data/spatial/infrasim-network/version_1.0/nodes_component_1.shp'
path_to_edges = '../data/spatial/infrasim-network/version_1.0/edges_component_1.shp'

n = []
x = []
y = []

count = 0
for i in tqdm(range(0,len(nodes_damaged))):
    if count < 99999999999999:
        # print(count)
        # init model
        run = jem(path_to_nodes,
                path_to_edges,
                path_to_flows,
                #timesteps=1,
                print_to_console=False,
                nodes_to_attack=nodes_damaged[0:i],
                #edges_to_attack=['edge_25297'],
                super_source=True,
                super_sink=False)
        
        # build model
        run.build()
        
        # run model
        run.optimise(print_to_console=False)
        
        # init results
        results = analyse(model_run=run)
        
        # get results
        try:
            n.append(nodes_damaged[0:i][-1])
        except:
            pass
        x.append(count)
        y.append(results.total_customers_affected())

    count = count + 1






r = pd.DataFrame({'x' : x, 'y' : y})
