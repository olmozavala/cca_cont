#!/bin/bash
# Activate virtual environment
source /AIRE/home/olmozavala/CODE/cca_cont/.venv/bin/activate

# Run the update script and save output to log file
python3 2_update_last_hour.py > /AIRE/home/olmozavala/CODE/cca_cont/hour_update.log 2>&1

# Deactivate virtual environment 
deactivate
