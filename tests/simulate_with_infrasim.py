# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 10:26:04 2021

@author: aqua
"""

import sys
sys.path.append('../')

from infrasim.model import *

nodes = '../data/demo/nodes_demo_processed.shp'
edges = '../data/demo/edges_demo_processed.shp'
flows = '../data/demo/csv/nodal_flows.csv'

# init model
jem = infrasim(nodes,edges,flows,
               timesteps=1,super_source=True,super_sink=True)


jem.build()



df = jem.edges

df = df[df.duplicated(subset=['from_id','to_id'], keep=False)]


arc_indicies      = jem.edge_indices[jem.indices].set_index(keys=jem.indices).index.to_list()