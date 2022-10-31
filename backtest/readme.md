`main.py`: main backtest file 

example command (ran from within backtest/): `python main.py --events ../experiments/init/simple -t no_oracle_guards`
- other parameters can be overriden (including protocol and geyser path)
- `-t` defines what trails you want to run 
- results will be in 'experiments/results/{events}/{trials}/...' 
  - this includes the geyser state results which are auto-extracted after each backtest

note: valid event folders require the following files 
- chs.csv: the clearing house states 
- events.csv: the events to backtest against 
- markets_json.csv: a json list of the serialized markets 

example: see 'experiments/init/simple/' which was made with the 'scripts/workspace/simple.py'

note: if you want to run multiple trials you should run the backtest/main.py once for each trial 

note: make sure `anchor localnet` works in protocol directory

note: run `ps aux | grep solana` to kill rogue validators

# generating sim events 
- run `workspace/collateral_check.py`
