#!/bin/bash

# Set the root path
ROOT_PATH="/AIRE/home/olmozavala/CODE/cca_cont"

# Activate virtual environment
source $ROOT_PATH/.venv/bin/activate
# CONDA:
#. $HOME/miniforge/etc/profile.d/conda.sh
#conda activate cca_cont

# Run the update script and save output to log file
python $ROOT_PATH/2_update_last_hour.py --date 2025-08-06 --hour 14 --hours 23

# Deactivate virtual environment 
deactivate
#conda deactivate
