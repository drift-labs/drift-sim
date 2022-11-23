## Drift-Sim: Simulation Framework for Drift-v2

The goals of the drift-sim repository is 
- research and prototype fast with a python implementation of the DAMM
- backtest events against the smart-contract protocol and view the results overtime 

## Overview

### Prototyping in Python 

The first component of the simulations include a python implementation of Drift's 
DAMM - most of the math/implementation used is also used in the python SDK. This 
includes Agents (which interact with the DAMM), Events (which are produced on each 
interaction with the DAMM), and State (the market, user, etc. structures). A full write
up on the python simulation setup can be found [here](https://www.notion.so/driftprotocol/Drift-Simulation-Framework-Guide-9bcff2bddf37445aa39c696bc3bfa705). The code of the python 
simulations can be found in `sim/`. 

### Backtesting Events against the Protocol 

While running agents against the python simulation we produce event files which list all the 
actions taken. For example, one looks like: 
```
event_name,timestamp,parameters
deposit_collateral,0.0,"{""deposit_amount"": 1998590197697, ""user_index"": 0, ""username"": ""LP""}"
add_liquidity,142.0,"{""market_index"": 0, ""token_amount"": 42554684114, ""user_index"": 1}"
settle_lp,183.0,"{""market_index"": 0, ""user_index"": 1}"
open_position,227.0,"{""direction"": ""long"", ""market_index"": 0, ""quote_amount"": 790100000, ""user_index"": 2}"
remove_liquidity,10000000000227.0,"{""lp_token_amount"": -1, ""market_index"": 0, ""user_index"": 1}"
close_position,10000000000228.0,"{""market_index"": 0, ""user_index"": 1}"
...
```

These events are then backtested on the protocol in `backtest/main.py` with the following event loop
which loops through each event and then executes it. 

```python 
for i in tqdm(range(len(events))):
  ix: TransactionInstruction
  if event.event_name == DepositCollateralEvent._event_name:
      continue

  elif event.event_name == MidSimDepositEvent._event_name:
      event = Event.deserialize_from_row(MidSimDepositEvent, event)
      assert event.user_index in user_chs, 'user doesnt exist'
      ch: SDKClearingHouse = user_chs[event.user_index]
      ix = await event.run_sdk(ch, admin_clearing_house, spot_mints)
      ix_args = event.serialize_parameters()
      print(f'=> {event.user_index} depositing...')

  elif event.event_name == OpenPositionEvent._event_name: 
      event = Event.deserialize_from_row(OpenPositionEvent, event)
      assert event.user_index in user_chs, 'user doesnt exist'

      ch: SDKClearingHouse = user_chs[event.user_index]
      ix = await event.run_sdk(ch, init_leverage, oracle_program, adjust_oracle_pre_trade=False)
      if ix is None: continue
      ix_args = place_and_take_ix_args(ix[1])
      print(f'=> {event.user_index} opening position...')

  elif event.event_name == ClosePositionEvent._event_name: 
      event = Event.deserialize_from_row(ClosePositionEvent, event)
      assert event.user_index in user_chs, 'user doesnt exist'

      ch: SDKClearingHouse = user_chs[event.user_index]
      ix = await event.run_sdk(ch, oracle_program, adjust_oracle_pre_trade=True)
      if ix is None: continue
      ix_args = place_and_take_ix_args(ix[1])
      print(f'=> {event.user_index} closing position...')
```

### Adding New Events

to include new events one would need to 
- create a new Event class in  `sim/events.py` which implements `run` (what it should do in the python 
implementation) and `run_sdk` (what it should do with tha actual protocol)
- and implement a new branch: `elif event.event_name == NEW_EVENT._event_name:` in the event loop 

Not required but usually you would also add an Agent which would produce the event you want and run a simulation with it -- see `scripts/workspace/` files to understand how it works with other agents. For example in simple.py, we create an agent which will Open and Close a position multiple times, add it to the list of agents, 
and then run the agents against the python implementation with the `run_trial(agents, ch, path)` call. 

```python 
agent = MultipleAgent(
    lambda: OpenClose.random_init(max_t[market_index], user_idx, market_index, short_bias=0.5),
    n_times, 
)
agents.append(agent)

# !! 
run_trial(agents, ch, path)
```

## Dev Setup

## install python packages 
```bash
# creates a virtualenv called "venv"
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# setup other submodules
bash setup.sh 
```

## install postgresql 

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
python simple.py # generate events.csv files of a simple market (results in experiments/init/simple)
cd ../../backtest 
python main.py --events ../experiments/init/simple -t no_oracle_guards # backtest the events against the v2 protocol 
ls ../experiments/results/simple/no_oracle_guards # behold the results 
```

## run the python simulation tests 

`python test.py` 

## update scripts

```
git submodule update --remote --merge
pip install driftpy/ --upgrade
```
