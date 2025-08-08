#!/bin/bash

# Set the root path
ROOT_PATH="/AIRE/home/olmozavala/CODE/cca_cont"

# Activate virtual environment
source $ROOT_PATH/.venv/bin/activate
# CONDA:
#. $HOME/miniforge/etc/profile.d/conda.sh
#conda activate cca_cont

# Function to get the previous month and year
get_previous_month() {
    local current_date=$(date +%Y-%m)
    local previous_month=$(date -d "$current_date -1 month" +%Y-%m)
    local year=$(echo $previous_month | cut -d'-' -f1)
    local month=$(echo $previous_month | cut -d'-' -f2)
    echo "$year $month"
}

# Function to run a single month update
run_update() {
    local year=$1
    local month=$2
    echo "Running: python3 3_update_by_month.py --year $year --month $month"
    python3 $ROOT_PATH/3_update_by_month.py --year $year --month $month > $ROOT_PATH/month_update.log 2>&1
}

# Export the function so it can be used by xargs
export -f run_update

# Parse command line arguments
if [ $# -eq 0 ]; then
    # Default to previous month
    read year month <<< $(get_previous_month)
    echo "No arguments provided. Using previous month: $month/$year"
elif [ $# -eq 2 ]; then
    # User provided year and month
    year=$1
    month=$2
    echo "Using provided year/month: $month/$year"
else
    echo "Usage: $0 [year month]"
    echo "  If no arguments provided, uses previous month from current date"
    echo "  Example: $0 2025 8"
    exit 1
fi

# Validate month and year
if ! [[ "$year" =~ ^[0-9]{4}$ ]]; then
    echo "Error: Year must be a 4-digit number"
    exit 1
fi

if ! [[ "$month" =~ ^[0-9]{1,2}$ ]] || [ "$month" -lt 1 ] || [ "$month" -gt 12 ]; then
    echo "Error: Month must be between 1 and 12"
    exit 1
fi

# Run the update for the specified month
run_update $year $month

echo "Update completed for $month/$year."
