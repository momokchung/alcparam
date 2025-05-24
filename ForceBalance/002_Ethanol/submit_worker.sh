#!/bin/bash
# Define your function
submit () {  

    hna=`hostname -s`

    # Source bashrc to load environment variables and paths
    source /user/kchung25/.bashrc

    # Properly initialize Conda and activate the environment
    source /user/kchung25/miniconda3-linux/bin/activate pyfb

    # Start the worker
    nohup /user/kchung25/miniconda3-linux/envs/pyfb/bin/work_queue_worker --cores=12 -t 864000 -d all -o $1/debug_$hna.out -s /scratch/ elf90.wustl.edu 9000 &> $1/$hna-log.txt &
}

# Nodes to skip
skip_nodes=(27 35 46 50 60 68 80 89 91 94 95 100)

for numb in `seq $1 $2`; do
    if [[ " ${skip_nodes[@]} " =~ " $numb " ]]; then
        echo "Skipping node elf$numb"
        continue
    fi

    echo "submitted work elf$numb"

    work_dir=$PWD/workers
    mkdir -p $work_dir

    ssh elf$numb "$(typeset -f submit); submit $work_dir"
done
