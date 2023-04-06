# Script README

This script simulates a financial market and clearing house using the drift sim framework.

1. The simulation creates a clearing house with one market and a simulation AMM.  
2. The script then sets up traders to deposit collateral and open long and short positions in the market.  
3. After five time steps, the script moves to a new price level where the market price increases by a factor of 4.  
4. The script then runs a liquidator agent who deposits funds in the spot market and begins liquidating positions.  
5. Finally, the script closes long positions and withdraws funds.  

# Requirements
Python 3.10  
Package versions: requirements.txt  

### Notes:  
Packages: solana, anchorpy, and soldana had some conflict issues

In requirements.txt, these versions were installed:  
solana==0.25.1  
solders==0.2.0  
anchorpy isn't listed

However, they weren't functional with the latest version of anchorpy. In order to run this script, sim_4x.py, with the necessary script dependencies from within the framework:

1. When anchorpy is installed, it automatically uninstalls and reinstalls the latest versions of solana, solders, among other dependent packages. This is a problem, because the solana and solders packages are then the wrong version, and some dependent scripts fail. Also, the latest version of anchorpy did not work with the framework and other dependent packages, however, version 0.15.0 did.  
2. After anchorpy is installed, I reverted versions of solana and solders to the versions listed in the requirements.txt.  
3. However, the solders package version did not work with dependent scripts. Updating solders to 0.14.4 worked with dependent scripts.

`pip install anchorpy==0.15.0`  
`pip install solana==0.25.1`  
`pip install solders==0.14.4`  


# Usage
To run the script, execute the following command:

`python3.10 sim_4x.py`


The script will output .csv files containing information about the events and clearing house objects generated during the simulation. These files will be saved in a new directory named sim_4x located in the experiments/init/ directory.

# Function  
`setup_ch(start_price, n_steps, quote_asset_reserve)`  

Sets up the clearing house with one market and a simulation AMM.

`start_price` (float): The starting price of the oracle.

`n_steps` (int): The number of steps to generate for the oracle. The current implementation does not use this, however, the code is commented there for a modified use case.

`quote_asset_reserve` (int): The amount of quote assets in the AMM reserve.

Returns:

ClearingHouse: The initialized clearing house.

`main()`  
Runs the main simulation and generates .csv files containing information about the events and clearing house objects generated during the simulation.

