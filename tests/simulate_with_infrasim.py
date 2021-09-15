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
flows = '../data/demo/csv/nodal_flows.csv'

# '../data/demo/nodes_demo_microsample_processed.shp'
# '../data/demo/edges_demo_microsample_processed.shp'

# '../data/demo/nodes_demo_processed.shp'
# '../data/demo/edges_demo_processed.shp'

# '../data/spatial/nodes_processed.shp'
# '../data/spatial/edges_processed.shp'

path_to_nodes = '../data/spatial/nodes_processed.shp'
path_to_edges = '../data/spatial/edges_processed.shp'

# init model
jem = infrasim(path_to_nodes,
               path_to_edges,
               flows,
               timesteps=1,
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
    
    
        

    # flows_to_shapefile(jem,filename='../data/demo/jem_results_edges.shp')
    
    # tag nodes that were supplied by super_source
    # jem = tag_super_source_flows(jem)
    
    # save
    # jem.nodes.to_file(driver='ESRI Shapefile', filename='../data/demo/jem_results_nodes.shp')
    

except:
    print('simulation failed')
    #jem.debug()
    

