## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

# %%
# %reload_ext autoreload
# %autoreload 2

import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
# sys.path.insert(0, './driftpy/src/')
sys.path.insert(0, '../../driftpy/src/')
sys.path.insert(0, '../../')

import driftpy
import os 
import datetime
import math 
import numpy as np 

from tqdm.notebook import tqdm 
from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

import json 
import numpy as np 
import pandas as pd

from sim.helpers import *
from sim.agents import * 

from sim.driftsim.clearing_house.math.pnl import *
from sim.driftsim.clearing_house.math.amm import *
from sim.driftsim.clearing_house.state import *
from sim.driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 

import pathlib 
import pandas as pd 

## EXPERIMENTS PATH 
path = pathlib.Path('../../experiments/init/simple')
path.mkdir(exist_ok=True, parents=True)
print(str(path.absolute()))

def setup_ch(base_spread=0, strategies='', n_steps=100):
    # market one 
    prices, timestamps = rand_heterosk_oracle(90, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        quote_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        funding_period=3600,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
        base_spread=base_spread,
        strategies=strategies,
    )
    market = SimulationMarket(amm=amm, market_index=0)
    markets = [market]
    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse(markets, fee_structure)

    ## save the markets!
    json_markets = [m.to_json(0) for m in markets]
    with open(path/'markets_json.csv', 'w') as f:
        json.dump(json_markets, f)

    return ch

seed = np.random.randint(0, 1e3)
# seed = 111
import random 
np.random.seed(seed)
random.seed(seed)

print('seed', seed)
ch = setup_ch(
    n_steps=20,
    base_spread=0,
)

n_lps = 1
n_traders = 1
n_times = 1
total_users = n_lps + n_traders
n_markets = len(ch.markets)

# init agents
max_t = [len(market.amm.oracle) for market in ch.markets]

agents = []

for market_index in range(n_markets):
    for user_idx in range(total_users):
        # trader agents (open/close)
        if user_idx < n_traders:
            agent = MultipleAgent(
                lambda: OpenClose.random_init(max_t[market_index], user_idx, market_index, short_bias=0.5),
                n_times, 
            )
            agents.append(agent)

        # LP agents (add/remove/settle) 
        elif user_idx < n_traders + n_lps:
            agent = MultipleAgent(
                lambda: AddRemoveLiquidity.random_init(max_t[market_index], user_idx, market_index, min_token_amount=100000),
                n_times, 
            )
            agents.append(agent)

            agent = SettleLP.random_init(max_t[market_index], user_idx, market_index)
            agents.append(agent)

        # settle pnl 
        agent = SettlePnL.random_init(max_t[market_index], user_idx, market_index)
        agents.append(agent)
    
print('#agents:', len(agents))

mark_prices = []
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

# record total collateral pre trades     
initial_collateral = compute_total_collateral(ch)

# run agents 
early_exit = False
abs_difference = 0 
settle_tracker = {}
for (_, user) in ch.users.items(): 
    settle_tracker[user.user_index] = False 

last_oracle_price = [-1] * n_markets

from tqdm import tqdm 
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

        if oracle_price != last_oracle_price and len(time_t_events) > 0:
            last_oracle_price[market.market_index] = oracle_price
            events.append(
                oraclePriceEvent(ch.time, market.market_index, oracle_price)
            )

    for e in time_t_events:
        ch = e.run(ch)

        # mark_prices.append(calculate_mark_price(market))    
        events.append(e)
        clearing_houses.append(copy.deepcopy(ch))

    ch = ch.change_time(1)

abs_difference, _events, _chs, _mark_prices = collateral_difference(ch, initial_collateral, verbose=False) 
events += _events
clearing_houses += _chs
# mark_prices += _mark_prices

if len(clearing_houses) > 0:
    ch = clearing_houses[-1]

differences.append(abs_difference)

# # if abs_difference > 1: 
# _ = [print(f"{e},") for e in events if e._event_name != 'null']

# print('---')
# _ = [print("\t", e._event_name) for e in events if e._event_name != 'null']

print('---')
print('number of events:', len(events))
print(f"seed = {seed}")
print("abs difference:", abs_difference)

# %%
lp_fee_payments = 0 
market_fees = 0 
market: SimulationMarket = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_fee_payments += position.lp_fee_payments
    market_fees += position.market_fee_payments

total_payments = lp_fee_payments + market.amm.total_fee_minus_distributions
print("fee diff:", abs(total_payments) - abs(market_fees))

# %%
lp_funding_payments = 0 
market_funding = 0 
market: SimulationMarket = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_funding_payments += position.lp_funding_payments
    market_funding += position.market_funding_payments
# total_payments = market.amm.lp_funding_payment + lp_funding_payments
total_payments = lp_funding_payments

print("funding diff", market_funding + total_payments)
print('net baa', clearing_houses[-1].markets[0].amm.base_asset_amount_with_amm)
print('---')

#%%
json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
df = pd.DataFrame(json_events)
df.to_csv(path/'events.csv', index=False)

json_chs = [e.to_json() for e in clearing_houses]
df = pd.DataFrame(json_chs)
df.to_csv(path/'chs.csv', index=False)

#%%