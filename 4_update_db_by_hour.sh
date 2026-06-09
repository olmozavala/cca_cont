#!/bin/bash

source "$(dirname "$0")/scripts/local_env.sh"

# Activate virtual environment
source "$ROOT_PATH/.venv/bin/activate"

# Run the update script
python "$ROOT_PATH/2_update_last_hour.py"

deactivate
