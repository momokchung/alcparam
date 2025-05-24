#!/bin/bash

# Function to kill any existing work_queue_worker process
killworker () {
    pids=$(ps aux | grep work_queue_worker | grep -v grep | awk '{print $2}')
    if [[ ! -z "$pids" ]]; then
        echo "Found work_queue_worker processes: $pids"
        for pid in $pids; do
            echo "Killing process $pid"
            kill -9 $pid
        done
    else
        echo "No work_queue_worker process found."
    fi
}

# List of nodes to skip
skip_nodes=(27 35 46 50 60 68 80 89 91 94 95 100)

# Loop over worker nodes
for numb in $(seq "$1" "$2"); do
    if [[ " ${skip_nodes[@]} " =~ " $numb " ]]; then
        echo "Skipping node elf$numb"
        continue
    fi

    echo "Attempting to kill worker on elf$numb"
    ssh elf$numb "$(typeset -f killworker); killworker"
done