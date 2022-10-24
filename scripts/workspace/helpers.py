
import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, '../../driftpy/src/')
sys.path.insert(0, '../../')

import json 
import numpy as np 
import pandas as pd
from tqdm import tqdm 
import pandas as pd 

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *
from driftpy.types import *
from driftpy.constants.numeric_constants import *

from sim.helpers import *
from sim.agents import * 

from sim.driftsim.clearing_house.math.pnl import *
from sim.driftsim.clearing_house.math.amm import *
from sim.driftsim.clearing_house.state import *
from sim.driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 
from pathlib import Path

def run_trial_events(events, ch, path: Path):
    path.mkdir(exist_ok=True, parents=True)

    ## save the initial markets!
    json_markets = [m.to_json(0) for m in ch.markets]
    with open(path/'markets_json.csv', 'w') as f:
        json.dump(json_markets, f)

    clearing_houses = []
    for e in tqdm(events):
        ch = ch.change_time(e.timestamp)
        ch = e.run(ch)

        clearing_houses.append(copy.deepcopy(ch))

    print('number of events:', len(events))

    # save trial results 
    json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
    df = pd.DataFrame(json_events)
    df.to_csv(path/'events.csv', index=False)

    json_chs = [e.to_json() for e in clearing_houses]
    df = pd.DataFrame(json_chs)
    df.to_csv(path/'chs.csv', index=False)


def run_trial(agents, ch, path):
    path.mkdir(exist_ok=True, parents=True)

    n_markets = len(ch.markets)
    max_t = [len(market.amm.oracle) for market in ch.markets]

    ## save the initial markets!
    json_markets = [m.to_json(0) for m in ch.markets]
    with open(path/'markets_json.csv', 'w') as f:
        json.dump(json_markets, f)

    print('#agents:', len(agents))

    events = []
    clearing_houses = []
    differences = []

    # setup agents
    for agent in agents:        
        events_i: list[Event] = agent.setup(ch)
        
        for event in events_i: 
            if event._event_name != 'null':
                ch = event.run(ch, verbose=False)
            events.append(event)
            clearing_houses.append(copy.deepcopy(ch))
            differences.append(0)
            
        ch.change_time(1)

    # run agents 
    settle_tracker = {}
    for (_, user) in ch.users.items(): 
        settle_tracker[user.user_index] = False 

    last_oracle_price = [-1] * n_markets

    for x in tqdm(range(max(max_t))):
        if x < ch.time:
            continue

        time_t_events = []
        for i, agent in enumerate(agents):
            events_i = agent.run(ch)
            for event_i in events_i:
                # tmp soln 
                # only settle once after another non-settle event (otherwise you get settle spam in the events)
                if event_i._event_name == 'settle_lp':
                    if settle_tracker[event_i.user_index]:
                        continue
                    else: 
                        settle_tracker[event_i.user_index] = True    
                elif event_i._event_name != 'null':
                    for k in settle_tracker.keys(): 
                        settle_tracker[k] = False
                
                if event_i._event_name != 'null':
                    time_t_events.append(event_i)
            
        # adjust oracle pre events
        for market in ch.markets:
            oracle_price = market.amm.oracle.get_price(ch.time)
            last_price = last_oracle_price[market.market_index]

            if oracle_price != last_price and len(time_t_events) > 0:
                last_oracle_price[market.market_index] = oracle_price
                events.append(
                    oraclePriceEvent(ch.time, market.market_index, oracle_price)
                )

        for e in time_t_events:
            ch = e.run(ch)

            events.append(e)
            clearing_houses.append(copy.deepcopy(ch))

        ch = ch.change_time(1)

    _, _events, _chs, _ = collateral_difference(ch, 0, verbose=False) 
    events += _events
    clearing_houses += _chs

    print('number of events:', len(events))

    # save trial results 
    json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
    df = pd.DataFrame(json_events)
    df.to_csv(path/'events.csv', index=False)

    json_chs = [e.to_json() for e in clearing_houses]
    df = pd.DataFrame(json_chs)
    df.to_csv(path/'chs.csv', index=False)
