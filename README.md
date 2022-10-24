## QuickStart

## install python packages 
```bash
# creates a virtualenv called "venv"
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# setup other submodules
bash setup.sh 
```
requirements / setup help:
- you'll need python 3.10
- to satisfy the requirements.tx you may need to install some 
- on mac OS, you can use homebrew
  - `brew install postgresql`

## file structure 
- `scripts/workspace/`: folder to produce events.csv/experiments by using agents or specific events against python protocol
- `backtest/main.py`: run an events.csv/experiment against the actual rust protocol 
- `sim/`: python simulation files (agents, events, python clearing_house, etc.)
- `solana-accountsdb-...`: geyser plugin to record changes in program account throughout the backtest and analyze the change in state
- `driftpy`: drift python sdk
- `experiments/`: folder to store initial data + events to start backtest in `init/` and the state over time in `results/` (after running backtest/main.py)

## backtest

```bash
cd scripts/workspace/
python simple.py # generate events.csv files of a simple market 
cd ../../backtest 
python main.py --events ../experiments/init/simple -t no_oracle_guards # backtest the events against the v2 protocol 
ls ../experiments/results/simple/no_oracle_guards # behold the results 
```

## run the tests 

`python test.py` 

## update scripts

```
git submodule update --remote --merge
pip install driftpy/ --upgrade
```
