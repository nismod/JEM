#!/bin/bash

#SBATCH --job-name=JEM
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --partition=devel
################SBATCH --mail-type=BEGIN,END  --mail-user=aman.majid@ouce.ox.ac.uk

module load Anaconda3//2020.11

source activate JEM

python test_run_jem.py
