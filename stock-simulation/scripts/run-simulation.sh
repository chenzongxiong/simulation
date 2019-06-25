#!/bin/bash

#SBATCH -J run-simulation
#SBATCH -D /home/zxchen/simulation/stock-simulation
#SBATCH -o ./tmp/run-simulations.out
#SBATCH --nodes=1
#SBATCH --mem=80G
#SBATCH --time=30-00:00:00
#SBATCH --partition=big
#SBATCH --mail-type=end
#SBATCH --mail-user=czxczf@gmail.com

hostname
source /home/zxchen/.venv3/bin/activate
python cli.py --sigma 110 --number-of-transaction 2000
