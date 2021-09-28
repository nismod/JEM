# -*- coding: utf-8 -*-
"""

    simulate_with_infrasim.py
    
        Script to carry out simulation with infrasim.
    
@amanmajid
"""

import sys
sys.path.append('../')

from infrasim.model import *
from infrasim.utils import *

#------------------------------------
# RUN MODEL

# define input files
path_to_flows = '../data/csv/generated_nodal_flows.csv'
path_to_nodes = '../data/spatial/nodes_processed.shp'
path_to_edges = '../data/spatial/edges_processed.shp'

# init model
jem = infrasim(path_to_nodes,
               path_to_edges,
               path_to_flows,
               #timesteps=1,
               print_to_console=False,
               #nodes_to_attack=['node_2009'],
               #edges_to_attack=['edge_712'],
               super_source=False,
               super_sink=False)

# build model
jem.build()

# run model
jem.run(print_to_console=True)


#------------------------------------
# PROCESS RESULTS OR DEBUG

try:
    
    # tag nodes that were supplied by super_source
    jem = tag_super_source_flows(jem)
    
    # save
    jem.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/jem_results_nodes.shp')
    flows_to_shapefile(jem,filename='../data/demo/jem_results_edges.shp')
    

except:
    print('simulation failed')
    jem.debug()
    
    
    
    
ss = jem.results_arcflows[jem.results_arcflows.from_id == 'super_source']
ss[ss.flow>0]