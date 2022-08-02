## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

# %%
# %reload_ext autoreload
# %autoreload 2

import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, './driftpy/src/')
sys.path.insert(0, '../driftpy/src/')
sys.path.insert(0, '../')

import driftpy
import os 
import datetime
import math 
from sim.agents import * 
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
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from sim.helpers import *

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 

def setup_ch(base_spread=0, strategies='', n_steps=100, n_users=2):
    prices, timestamps = random_walk_oracle(1, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=1_000_000 * 1e13,
        quote_asset_reserve=1_000_000 * 1e13,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*1e3),
        base_spread=base_spread,
        strategies=strategies,
        # base_asset_amount_step_size=0,
        # minimum_quote_asset_trade_size=0,
    )
    market = SimulationMarket(amm=amm, market_index=0)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    ch = ClearingHouse([market], fee_structure)

    for i in range(n_users):
        ch = DepositCollateralEvent(
            user_index=i, 
            deposit_amount=1_000 * QUOTE_PRECISION, 
            timestamp=ch.time,
        ).run(ch)

    return ch

#%%
seed = np.random.randint(0, 1e3)
# seed = 111
import random 
np.random.seed(seed)
random.seed(seed)

print('seed', seed)
ch = setup_ch(
    n_steps=100,
    base_spread=0,
)
market: SimulationMarket = ch.markets[0]

n_lps = 10
n_trades = 10

sim = RandomSimulation(ch)
agents = []

# these are classic add remove full lps
agents += [
    sim.generate_lp(i, 0) for i in range(n_lps)
]
# these are classic add remove full lps -- laid on top add/remove will be full or partial
agents += [
    sim.generate_lp(i, 0) for i in range(n_lps)
]

# let the lps settle
agents += [
    sim.generate_lp_settler(i, 0) for i in range(n_lps)
]

# let the lps trade
agents += [
    sim.generate_trade(i, 0) for i in range(n_lps)
]

# normal traders open/close 
agents += [
    sim.generate_trade(i, 0) for i in range(n_lps, n_lps+n_trades)
]
# random open close == more open close trades of a single trader
agents += [
    sim.generate_trade(i, 0) for i in range(n_lps, n_lps+n_trades)
]
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

from tqdm import tqdm 
for x in tqdm(range(len(market.amm.oracle))):
    if x < ch.time:
        continue
    
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
                ch = event_i.run(ch)
                    
                mark_prices.append(calculate_mark_price(market))    
                events.append(event_i)
                clearing_houses.append(copy.deepcopy(ch))

                (abs_difference, _) = collateral_difference(ch, initial_collateral, verbose=False)[0]
                differences.append(abs_difference)
        
            if abs_difference > 1:
                print('blahhh', abs_difference)
                early_exit = True 
                break 


        if early_exit: 
            break

    if early_exit: 
        break     
    
    ch = ch.change_time(1)

abs_difference, _events, _chs, _mark_prices = collateral_difference(ch, initial_collateral, verbose=False) 
events += _events
clearing_houses += _chs
mark_prices += _mark_prices

if len(clearing_houses) > 0:
    ch = clearing_houses[-1]

differences.append(abs_difference)

# # if abs_difference > 1: 
# _ = [print(f"{e},") for e in events if e._event_name != 'null']

print('---')
_ = [print("\t", e._event_name) for e in events if e._event_name != 'null']

print('---')
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
total_payments = market.amm.lp_funding_payment + lp_funding_payments

print("funding diff", market_funding + total_payments)
print('net baa', clearing_houses[-1].markets[0].amm.net_base_asset_amount)
print('---')

#%%
import pathlib 
import pandas as pd 

path = pathlib.Path('sim-results/tmp5')
path.mkdir(exist_ok=True, parents=True)
print(str(path.absolute()))

#%%
json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
df = pd.DataFrame(json_events)
df.to_csv(path/'events.csv', index=False)

json_chs = [e.to_json() for e in clearing_houses]
df = pd.DataFrame(json_chs)
df.to_csv(path/'chs.csv', index=False)

#%%
#%%
#%%


# #%%
# #%%
# #%%
# plt.plot([d for d in differences if d != 0])
# print(np.unique(differences))

# # #%%
# # import matplotlib.colors as mcolors
# # cmap = mcolors.BASE_COLORS
# # keys = list(cmap.keys())
# #
# # mark_change = np.array(mark_prices) - mark_prices[0]
# # above = True 
# # plt.plot(mark_change)
# # for i, e in enumerate(events): 
# #     if e._event_name != 'null':
# #         color = cmap[keys[e.user_index % len(keys)]]
# #         plt.scatter(i, mark_change[i], color=color)
# #         plt.text(i+0.5, mark_change[i], e._event_name, rotation=90)
# #
# #%%
# def pprint(x):
#     print("\t", x)

# _ = [pprint(e) for e in events if e._event_name != 'null']
# # _ = [print(e._event_name, e.user_index) for e in events if e._event_name != 'null']

# #%%
# _events = [e for e in events if e._event_name != 'null']
# print(len(_events))

# np.random.seed(seed)
# ch = setup_ch(
#     base_spread=0, 
#     strategies='',
#     n_steps=100,
# )

# init_total_collateral = 0 
# for e in _events: 
#     if e._event_name != 'deposit_collateral' and init_total_collateral == 0:
#         init_total_collateral = compute_total_collateral(ch)     
        
#     # ch.time = e.timestamp
#     ch = e.run(ch)
    
# # recompute collateral 
# end_total_collateral = compute_total_collateral(ch)

# # ensure collateral still adds up 
# abs_difference = abs(init_total_collateral - end_total_collateral)
# abs_difference, init_total_collateral, end_total_collateral

# #%%
# json_chs = [
#     ch.to_json() for ch in tqdm(clearing_houses)
# ]
# results = pd.DataFrame(json_chs)
# keep_columns = results.columns
# keep_columns = [c for c in keep_columns if results[c].dtype == float or results[c].dtype == int]
# # keep_columns = [c for c in keep_columns if 'u1' in c] # only lp 
# filtered_df = results[keep_columns]
# filtered_df.plot()

# #%%
# df = pd.DataFrame(data=clearing_houses[-1].to_json(), index=[0])
# df.plot()

#%%
#%%
#%%
