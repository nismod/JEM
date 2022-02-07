#!/bin/bash

#SBATCH --job-name=JEM
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --partition=interactive
#SBATCH --mail-type=BEGIN,END  --mail-user=aman.majid@ouce.ox.ac.uk
#SBATCH --array=1-20

module load Gurobi/9.1.2-GCCcore-10.3.0
module load Anaconda3//2020.11

source activate jem_model

python run_edge_impact_assessment.py $SLURM_ARRAY_TASK_ID
