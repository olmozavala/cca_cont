#!/bin/bash

# Set the root path
ROOT_PATH="/AIRE/home/olmozavala/CODE/cca_cont"

# Export ROOT_PATH so it's available in child processes
export ROOT_PATH

# Activate virtual environment
source $ROOT_PATH/.venv/bin/activate

# Set the minimum and maximum year
min_year=2010
max_year=2026

# Maximum number of parallel jobs
max_parallel=4

# Function to run a single month update
run_update() {
    local year=$1
    local month=$2
    echo "Running: $ROOT_PATH/.venv/bin/python $ROOT_PATH/3_update_by_month.py --year $year --month $month"
    # python3 $ROOT_PATH/3_update_by_month.py --year $year --month $month > $ROOT_PATH/month_update.log 2>&1
    $ROOT_PATH/.venv/bin/python $ROOT_PATH/3_update_by_month.py --year $year --month $month 
}

# Export the function so it can be used by xargs
export -f run_update

# Build the list of year/month combinations
combinations=()
for year in $(seq $min_year $max_year); do
    for month in $(seq 1 12); do
        combinations+=("$year $month")
    done
done

# Run up to $max_parallel jobs in parallel using xargs
printf "%s\n" "${combinations[@]}" | xargs -n 2 -P $max_parallel -I {} bash -c 'run_update {}'

wait

echo "All updates completed."
