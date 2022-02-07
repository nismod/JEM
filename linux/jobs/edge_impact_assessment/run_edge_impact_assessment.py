'''

run_edge_impact_assessment.py

    This script damages edges one-at-a-time (single point failure analysis) to evaluate
    the number of sinks damaged. 

'''
print('')
print('')
print('-----------------------------------------------------------------')
print('run_edge_impact_assessment.py')
print('')


#--------------
# GLOBAL VARIABLES

restart_mode = True
save_after_iterations = 500
time_script = True
max_iterations = 90000
number_of_nodes = 20


#--------------
# RUN

print('Config')
print('------')
print('Restart mode: ' + str(restart_mode))
print('Save archive after ' + str(save_after_iterations) + ' iterations')
print('')

print('Log')
print('------')

import os
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
output_dir    = '../../outputs/edge_impact_assessment/'

# read edge data
edges = gpd.read_file(path_to_edges)

#reindex node
user_input = int(sys.argv[1:][0])
if not user_input:
    output_file_path = 'edge_impact_assessment_'
else:
    def edge_indexer(input_arg):
        '''return indices to use to sample nodes dataframe for batch run
        '''
        a = np.linspace(0,max_iterations,number_of_nodes)
        return int(a[input_arg-1]),int(a[input_arg])
        
    n1,n2 = edge_indexer(user_input)
    edges = edges.iloc[n1:n2].reset_index(drop=True)
    output_file_path = 'edge_impact_assessment_batch_' + str(user_input) 

if not restart_mode:
    pass
else:
    print('initiating restart mode...')
    try:
        batch_max_iteration = [i for i in os.listdir(output_dir + 'archive/') if output_file_path in i]
        batch_max_iteration = [i.split('_')[6] for i in batch_max_iteration]
        batch_max_iteration = [int(i.split('.')[0]) for i in batch_max_iteration]
        batch_max_iteration = max(batch_max_iteration)
    except:
        print('Error! could not read archive from previous run')

    # define filename
    batch_filename = output_dir + 'archive/' + output_file_path + '_iteration_' + str(batch_max_iteration) + '.csv'
    print('found previous archive ' + output_file_path + '_iteration_' + str(batch_max_iteration) + '.csv')

    # read in last archive
    previous_archive = pd.read_csv(batch_filename)

    # get edges not yet analysed
    edges_analysed = previous_archive.attacked_edge_id.unique().tolist()
    edges = edges.loc[~edges.id.isin(edges_analysed)].reset_index(drop=True)

# read previous archive
#edges_to_attack = edges.head(3).id.to_list()
edges_to_attack = edges.id.to_list()

print('loaded edges to attack')

if not restart_mode:
    results_dataframe = []
    count = 1
else:
    results_dataframe = previous_archive.copy()
    count = previous_archive.iteration_number.max() + 1

print('beginning loop...')
for i in range(0,len(edges_to_attack)):
    if not time_script:
        pass
    else:
        start_time = time.time()
    # ignore iteration if sink
    attacked_edge_type = edges.loc[edges.id==edges_to_attack[i],'asset_type'].iloc[0]
    if attacked_edge_type == 'sink':
        # create blank results
        df = pd.DataFrame({'iteration_number'           : count,
                           'attacked_edge_id'           : edges_to_attack[i],
                           'affected_node_id'           : [np.nan],
                           'attacked_edge_type'         : attacked_edge_type,
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
                  #nodes_to_attack=[edges_to_attack[i]],
                  edges_to_attack=[edges_to_attack[i]],
                  super_source=True,
                  super_sink=False)
    
        # build model
        run.build()
        # run model
        run.optimise(print_to_console=False)
        # init results
        results = analyse(model_run=run)

        # get results
        nodes_with_shortfall = results.nodes_with_shortfall().node.to_list()
        # if df is empty, we append blank results
        if results.nodes_with_shortfall().empty == True:
            df = pd.DataFrame({'iteration_number'           : count,
                             'attacked_edge_id'             : edges_to_attack[i],
                             'affected_node_id'             : [np.nan],
                             'attacked_edge_type'           : attacked_edge_type,
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
            df['attacked_edge_id']      = edges_to_attack[i]
            df['attacked_edge_type']   = attacked_edge_type
            # change column naming
            df['iteration_number']      = count
            df['population_affected']   = df['population']
            df['demand_affected']       = df['demand']
            # reindex
            df = df[['iteration_number',
                     'attacked_edge_id',
                     'affected_node_id',
                     'attacked_edge_type',
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
    if not restart_mode:
        results_dataframe.append(df)
    else:
        results_dataframe = results_dataframe.append(df,ignore_index=True)
        
    # append counter
    print('completed iteration ' + str(count) + ' of ' + str(len(edges_to_attack)))
    # save
    if count % save_after_iterations == 0:
        
        if not restart_mode:
            tmp_df = pd.concat(results_dataframe,ignore_index=True)
        else:
            tmp_df = results_dataframe.copy()

        # check if archive dir exists
        if not os.path.isdir(output_dir + 'archive/'):
            os.makedirs(output_dir + 'archive/')
            
        # save archive
        tmp_df.to_csv(output_dir + 'archive/' + output_file_path + '_iteration_' + str(count) + '.csv',index=False)
        print('saved archive at iteration number ' + str(count))
    count = count + 1

print('done')

print('Saving results...')

if not restart_mode:
    results_dataframe = pd.concat(results_dataframe,ignore_index=True)
else:
    pass

results_dataframe.to_csv(output_dir + output_file_path + '.csv',index=False)

print('done')

print('-----------------------------------------------------------------')