'''

single_point_failure_postprocess.py

    This script is used to conduct postprocessing on the results from single-point
    failure analyses of nodes and edges (../linux/outputs/<node/edge>_impact_assessment)

'''

import os
import pandas as pd

# ---------------
# GLOBAL VARS

output_path     = '../data/single_point_failure/'
node_path       = '../linux/outputs/node_impact_assessment/' 
edge_path       = '../linux/outputs/edge_impact_assessment/'

# ---------------
# NODES

# read results and merge into one df
merged_results = []
for i in os.listdir(node_path):
    if '.csv' in i:
        d = pd.read_csv(node_path + i)
        prev_cols = list(d.columns)
        d['batch_number'] = int(i.split('_')[4])
        d = d[ ['batch_number'] + prev_cols ]
        merged_results.append(d)
        
# concat
merged_results = pd.concat(merged_results,ignore_index=True)
merged_results = merged_results.sort_values(['batch_number','iteration_number']).reset_index(drop=True)
# remove duplicates
merged_processed = merged_results.copy()
prev_cols =  merged_processed.columns

merged_processed = merged_processed.groupby(['attacked_node_id',
                                             'affected_node_id'],as_index=False,dropna=False).first()

#merged_processed = merged_processed.drop(['batch_number','iteration_number'],axis=1)
merged_processed = merged_processed.sort_values(['batch_number','iteration_number'])
merged_processed = merged_processed[prev_cols].reset_index(drop=True)

# save
merged_processed.to_csv(output_path + 'single_point_failure_results_nodes.csv',index=False)

# ---------------
# EDGES