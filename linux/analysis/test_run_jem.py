print('------------------------------------------------')
print('Starting...')

print('importing modules...')

import pandas as pd
import os
from tqdm import tqdm
import sys
sys.path.append('../')

print('done')

print('importing jet modules...')
from jem.model import jem
from jem.analyse import analyse
from jem.utils import *

print('done')

# define input files
path_to_flows = '../data/generated_nodal_flows.csv'
path_to_nodes = '../data/nodes.shp'
path_to_edges = '../data/edges.shp'

print('defining model...')

run = jem(
	path_to_nodes,
        	path_to_edges,
	path_to_flows,
	#timesteps=1,
	print_to_console=True,
	#nodes_to_attack=nodes_damaged[0:i],
	#edges_to_attack=['edge_25297'],
	#super_source=True,
	super_sink=False)

print('done')

# build model
print('building Gurobi model...')
run.build()
print('done')

# run model
print('starting optimisation...')
run.optimise(print_to_console=False)
print('done')

# init results
print('fetching results...')
results = analyse(model_run=run)
print('done')
print('Completed: script finished without errors')
print('')
print('------------------------------------------------')