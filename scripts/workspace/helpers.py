
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


def run_trial_events(events, ch: ClearingHouse, path: Path):
    path.mkdir(exist_ok=True, parents=True)

    ## save the initial markets!
    json_markets = [m.to_json(0) for m in ch.markets]
    with open(path/'markets_json.csv', 'w') as f:
        json.dump(json_markets, f)

    ## save spot markets 
    json_spot_market = [{
        'init_price': int(sm.oracle.prices[0])
    } for sm in ch.spot_markets]
    with open(path/'spot_markets_json.csv', 'w') as f:
        json.dump(json_spot_market, f)

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
    print('#agents:', len(agents))

    ch: ClearingHouse
    ## save the initial markets!
    json_markets = [m.to_json(0) for m in ch.markets]
    with open(path/'markets_json.csv', 'w') as f:
        json.dump(json_markets, f)

    ## save spot markets 
    json_spot_market = [{
        'init_price': int(sm.oracle.prices[0])
    } for sm in ch.spot_markets]
    with open(path/'spot_markets_json.csv', 'w') as f:
        json.dump(json_spot_market, f)

    @dataclass
    class _Oracle: 
        oracle: Oracle
        is_perp: bool 
        index: int

    oracles = []
    for market in ch.markets: 
        o = _Oracle(
            market.amm.oracle, 
            True, 
            market.market_index
        )
        oracles.append(o)

    for i, spot_market in enumerate(ch.spot_markets):
        o = _Oracle(
            spot_market.oracle, 
            False, 
            i+1, # zero is reserved
        )
        oracles.append(o)
    last_oracle_price = [-1] * len(oracles)

    max_t = [len(o.oracle) for o in oracles]
    print('max_t:', max_t)

    events = []
    clearing_houses = []
    differences = []

    def adjust_oracle_prices():
        # adjust oracle pre events
        _oracle: _Oracle
        for i, _oracle in enumerate(oracles):
            oracle_price = _oracle.oracle.get_price(ch.time)
            last_price = last_oracle_price[i]

            if oracle_price != last_price:
                last_oracle_price[i] = oracle_price
                if _oracle.is_perp:
                    event = PerpOracleUpdateEvent(ch.time, _oracle.index, oracle_price)
                else: 
                    event = SpotOracleUpdateEvent(ch.time, _oracle.index, oracle_price)
                events.append(event)

    # setup agents
    for agent in agents:        
        events_i: list[Event] = agent.setup(ch)
        
        for event in events_i: 
            if event._event_name != 'null':
                ch = event.run(ch, verbose=False)
                events.append(event)
                clearing_houses.append(copy.deepcopy(ch))
                differences.append(0)
        
        # adjust_oracle_prices()
        ch = ch.change_time(1)

    # run agents 
    settle_tracker = {}
    for (_, user) in ch.users.items(): 
        settle_tracker[user.user_index] = False 

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
            

        update_oracle_flag = False
        e: Event
        for e in time_t_events:
            ch = e.run(ch)

            if e._event_name != 'liquidate':
                update_oracle_flag = True

            events.append(e)
            clearing_houses.append(copy.deepcopy(ch))

        if len(time_t_events) > 0 and update_oracle_flag:
            adjust_oracle_prices()
        
        ch = ch.change_time(1)

    _, _events, _chs, _ = collateral_difference(ch, 0, verbose=False) 
    events += _events
    clearing_houses += _chs

    # remove multiple liquidations 
    _events = []
    last_was_liq = False
    for e in events: 
        if e._event_name == 'liquidate':
            if last_was_liq: 
                continue
            last_was_liq = True
        else: 
            last_was_liq = False
        _events.append(e)
    events = _events

    print('number of events:', len(events))

    # save trial results 
    def save_events(events):
        json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
        df = pd.DataFrame(json_events)
        df.to_csv(path/'events.csv', index=False)
    save_events(events)

    json_chs = [e.to_json() for e in clearing_houses]
    df = pd.DataFrame(json_chs)
    df.to_csv(path/'chs.csv', index=False)

    return events, save_events
