#!/bin/bash

# Set the root path
ROOT_PATH="/AIRE/home/olmozavala/CODE/cca_cont"

# Activate virtual environment
source $ROOT_PATH/.venv/bin/activate

# Run the update script and save output to log file
python3 $ROOT_PATH/2_update_last_hour.py > $ROOT_PATH/hour_update.log 2>&1

# Deactivate virtual environment 
deactivate
