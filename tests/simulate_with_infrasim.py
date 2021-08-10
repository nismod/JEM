# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 10:26:04 2021

@author: aqua
"""

import sys
sys.path.append('../')

from infrasim.model import *

# nodes = '../data/demo/nodes_demo_microsample_processed.shp'
# edges = '../data/demo/edges_demo_microsample_processed.shp'

nodes = '../data/demo/nodes_demo_processed.shp'
edges = '../data/demo/edges_demo_processed.shp'

flows = '../data/demo/csv/nodal_flows.csv'

# init model
jem = infrasim(nodes,edges,flows,
               timesteps=1,super_source=False,super_sink=False)


jem.build()
jem.run()

try:
    
    r = jem.results_arcflows
    r = r[r.to_id != 'super_sink'].reset_index(drop=True)
    
    #---
    # Export results to GIS
    
    edges = gpd.read_file('../data/demo/edges_demo_microsample_processed.shp')
    nodes = gpd.read_file('../data/demo/nodes_demo_microsample_processed.shp')
    
    # concat
    rr = pd.concat([edges,r],axis=1).sort_values(by='id')
    edges = edges.sort_values(by='id')
    
    # add to edges
    edges['Result'] = rr.Value
    
    # save
    edges.to_file(driver='ESRI Shapefile', filename='../data/demo/model_results.shp')
    
except:
    jem.debug()
    
