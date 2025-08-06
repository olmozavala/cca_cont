#!/bin/bash

# Set the minimum and maximum year
min_year=2000
max_year=2025

# Maximum number of parallel jobs
max_parallel=4

# Function to run a single month update
run_update() {
    local year=$1
    local month=$2
    echo "Running: python3 3_update_by_month.py --year $year --month $month"
    python3 3_update_by_month.py --year $year --month $month
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
printf "%s\n" "${combinations[@]}" | xargs -n 2 -P $max_parallel bash -c 'run_update "$0" "$1"' 

wait

echo "All updates completed."
