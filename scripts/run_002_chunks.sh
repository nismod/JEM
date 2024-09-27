#!/bin/bash
#SBATCH --job-name=multi_failure
#SBATCH --output=multi_failure_%A_%a.out
#SBATCH --error=multi_failure_%A_%a.err
#SBATCH --array=0-100
#SBATCH --time=02:00:00

# Print this sub-job's task ID
echo "SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID

# Micromamba setup
# Weird workaround I found to get micromamba to work - maybe a temporary issue?
export MAMBA_EXE='/soge-home/users/cenv1068/.local/bin/micromamba';
export MAMBA_ROOT_PREFIX='/soge-home/users/cenv1068/micromamba';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"
fi
unset __mamba_setup
# end of workaround
# source /soge-home/users/cenv1068/micromamba/etc/profile.d/micromamba.sh
# micromamba activate jem-env
# /soge-home/users/cenv1068/micromamba/bin/micromamba activate jem-env
# conda init
# conda activate jem-env

# Load Gurobi module
module load gurobi

# Set the Gurobi license file environment variable
export GRB_LICENSE_FILE=/soge-home/users/cenv1068/gurobi.lic

# Parameters
ARRAY_SIZE=100

# Run the Python script
echo "Starting task $SLURM_ARRAY_TASK_ID at $(date)"
python 002-multi-edge-node-failure.py /soge-home/projects/mistral/jamaica-ccri/ 
 $SLURM_ARRAY_TASK_ID 
 $ARRAY_SIZE
if [ $? -ne 0 ]; then
    echo "Error: Python script failed for SLURM_ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID" >&2
    exit 1
fi

echo "Completed task $SLURM_ARRAY_TASK_ID at $(date)"
