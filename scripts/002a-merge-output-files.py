import pandas as pd
import os
import glob

folder_path = '/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/node_impact_assessment_batch_*'

all_results = []

for file_path in glob.glob(folder_path):
    if os.path.isfile(file_path):
        result = pd.read_csv(file_path)
        all_results.append(result)

all_results = pd.concat(all_results, ignore_index = True)
all_results.to_csv("/soge-home/projects/mistral/jamaica-ccri/results/grid_failures/ox_jem_multi_network_impact_assessment.csv")
