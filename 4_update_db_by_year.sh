#!/bin/bash

source "$(dirname "$0")/scripts/local_env.sh"

# Activate virtual environment
source "$ROOT_PATH/.venv/bin/activate"

min_year=2010
max_year=2026
max_parallel=4

run_update() {
    local year=$1
    local month=$2
    echo "Running: $ROOT_PATH/.venv/bin/python $ROOT_PATH/3_update_by_month.py --year $year --month $month"
    "$ROOT_PATH/.venv/bin/python" "$ROOT_PATH/3_update_by_month.py" --year "$year" --month "$month"
}

export -f run_update

combinations=()
for year in $(seq "$min_year" "$max_year"); do
    for month in $(seq 1 12); do
        combinations+=("$year $month")
    done
done

printf "%s\n" "${combinations[@]}" | xargs -n 2 -P "$max_parallel" -I {} bash -c 'run_update {}'

wait

echo "All updates completed."

deactivate
