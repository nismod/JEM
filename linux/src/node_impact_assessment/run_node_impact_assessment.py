'''

run_sink_impact_assessment.py

    This script damages nodes one-at-a-time (single point failure analysis) to evaluate
    the number of sinks damaged. It is a computationally intensive script.

'''
print('')
print('')
print('-----------------------------------------------------------------')
print('run_sink_impact_assessment.py')
print('')


#--------------
# GLOBAL VARIABLES

restart_mode = False
save_after_iterations = 500
time_script = True
max_iterations = 45000
number_of_nodes = 19



#--------------
# RUN

print('Config')
print('------')
print('Restart mode: ' + str(restart_mode))
print('Save archive after ' + str(save_after_iterations) + ' iterations')
print('')

print('Log')
print('------')

import sys
import time
import pandas as pd
from tqdm import tqdm

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import sys
sys.path.append('../../')

from jem.model import jem
from jem.analyse import analyse
from jem.utils import *

print('imported modules')

# define input files
path_to_flows = '../../data/generated_nodal_flows.csv'
path_to_nodes = '../../data/nodes.shp'
path_to_edges = '../../data/edges.shp'

nodes = gpd.read_file(path_to_nodes)

#reindex node
user_input = int(sys.argv[1:][0])
if not user_input:
    output_file_path = '../../outputs/node_impact_assessment/node_impact_assessment_'
else:
    def node_indexer(input_arg):
        '''return indices to use to sample nodes dataframe for batch run
        '''
        a = np.linspace(0,max_iterations,number_of_nodes)
        return int(a[input_arg-1]),int(a[input_arg])
        
    n1,n2 = node_indexer(user_input)
    nodes = nodes.iloc[n1:n2].reset_index(drop=True)
    output_file_path = '../../outputs/node_impact_assessment/node_impact_assessment_batch_' + str(user_input) + '_iteration_'

#nodes_to_attack = nodes.head(4).id.to_list()
nodes_to_attack = nodes.id.to_list()
#nodes_to_attack = ['node_1','node_2','node_80']

print('loaded nodes to attack')

results_dataframe = []
count = 1
print('beginning loop...')
for i in range(0,len(nodes_to_attack)):
    if not time_script:
        pass
    else:
        start_time = time.time()
    # ignore iteration if sink
    attacked_node_type = nodes.loc[nodes.id==nodes_to_attack[i],'asset_type'].iloc[0]
    if attacked_node_type == 'sink':
        # create blank results
        df = pd.DataFrame({'iteration_number'           : count,
                           'attacked_node_id'           : nodes_to_attack[i],
                           'affected_node_id'           : [np.nan],
                           'attacked_node_type'         : attacked_node_type,
                           'affected_node_type'         : [np.nan],
                           'total_nodes_affected'       : [np.nan],
                           'population_affected'        : [np.nan],
                           'demand_affected'            : [np.nan],})
    else:
        # run model
        run = jem(path_to_nodes,
                path_to_edges,
                path_to_flows,
                #timesteps=1,
                print_to_console=False,
                nodes_to_attack=[nodes_to_attack[i]],
                #edges_to_attack=['edge_25297'],
                super_source=True,
                super_sink=False)
    
        # build model
        run.build()
        # run model
        run.optimise(print_to_console=False)
        # init results
        results = analyse(model_run=run)

        print('super source flow: ' + str(results.edge_flows.loc[results.edge_flows.from_id == 'super_source'].flow.sum()))

        # get results
        nodes_with_shortfall = results.nodes_with_shortfall().node.to_list()
        # if df is empty, we append blank results
        if results.nodes_with_shortfall().empty == True:
            df = pd.DataFrame({'iteration_number'           : count,
                             'attacked_node_id'             : nodes_to_attack[i],
                             'affected_node_id'             : [np.nan],
                             'attacked_node_type'           : attacked_node_type,
                             'affected_node_type'           : [np.nan],
                             'total_nodes_affected'         : [np.nan],
                             'population_affected'          : [np.nan],
                             'demand_affected'              : [np.nan],})
        else:
            population = results.get_population_at_nodes(nodes_with_shortfall,col_id='affected_node_id')
            demand = results.get_demand_at_nodes(nodes_with_shortfall,col_id='affected_node_id')
            node_types = results.nodes.loc[results.nodes.id.isin(nodes_with_shortfall),'asset_type'].to_list()
            # merge
            df = population.merge(demand,on='affected_node_id')
            # add node types
            df['affected_node_type'] = node_types
            # add total number of sinks impacted
            df['total_nodes_affected']  = df.shape[0]
            # add damaged node id
            df['attacked_node_id']      = nodes_to_attack[i]
            df['attacked_node_type']    = attacked_node_type
            # change column naming
            df['iteration_number']      = count
            df['population_affected']   = df['population']
            df['demand_affected']       = df['demand']
            # reindex
            df = df[['iteration_number',
                     'attacked_node_id',
                     'affected_node_id',
                     'attacked_node_type',
                     'affected_node_type',
                     'total_nodes_affected',
                     'population_affected',
                     'demand_affected']]

    end_time = time.time()
    time_difference = end_time - start_time
    if not time_script:
        pass
    else:
        df['iteration_time_seconds'] = time_difference

    # append
    results_dataframe.append(df)
    # append counter
    print('completed iteration ' + str(count) + ' of ' + str(len(nodes_to_attack)))
    # save
    if count % save_after_iterations == 0:
        tmp_df = pd.concat(results_dataframe,ignore_index=True)
        tmp_df.to_csv(output_file_path + str(count) + '.csv',index=False)
        print('saved archive at iteration number ' + str(count))
    count = count + 1

print('done')

print('Saving results...')
results_dataframe = pd.concat(results_dataframe,ignore_index=True)
results_dataframe.to_csv(output_file_path + '.csv',index=False)
print('done')

print('-----------------------------------------------------------------')