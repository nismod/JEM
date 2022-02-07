#!/bin/bash

#SBATCH --job-name=JEM
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=interactive
#SBATCH --mail-type=BEGIN,END  --mail-user=aman.majid@ouce.ox.ac.uk
#SBATCH --array=1-19

module load Gurobi/9.1.2-GCCcore-10.3.0
module load Anaconda3//2020.11

source activate jem_model

python run_node_impact_assessment.py $SLURM_ARRAY_TASK_ID