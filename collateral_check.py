## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

# %%
%reload_ext autoreload
%autoreload 2

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

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.lib import *

from sim.helpers import close_all_users, random_walk_oracle, compute_total_collateral
from sim.events import * 
from sim.agents import * 

def setup_ch(base_spread=0, strategies='', n_steps=100, n_users=2):
    prices, timestamps = random_walk_oracle(1, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = AMM(
        oracle=oracle, 
        base_asset_reserve=1_000_000 * 1e13,
        quote_asset_reserve=1_000_000 * 1e13,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*1e3),
        base_spread=base_spread,
        strategies=strategies,
    )
    market = Market(amm)
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
class RandomSimulation():
    def __init__(self, ch: ClearingHouse) -> None:
        self.ch = ch 
        market: Market = ch.markets[0]
        self.max_t = len(market.amm.oracle)

        peg = market.amm.peg_multiplier / PEG_PRECISION
        sqrt_k = market.amm.sqrt_k / 1e13
        self.full_amm_position_quote = sqrt_k * peg * 2 * 1e6

    def generate_lp_settler(self, user_index, market_index) -> Agent:
        return SettleLP(
            user_index, 
            market_index, 
            every_x_steps=1, # tmp
        )

    def generate_lp(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, max_t)
        dur = np.random.randint(0, max_t // 2)
        amount = np.random.randint(0, full_amm_position_quote // (n_lps + 10))
        return LP(
            lp_start_time=start,
            lp_duration=dur, 
            deposit_amount=amount, 
            user_index=user_index, 
            market_index=market_index
        )

    def generate_trade(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, max_t)
        dur = np.random.randint(0, max_t // 2)
        amount = np.random.randint(0, 100_000)
        
        return OpenClose(
            start_time=start,
            duration=dur, 
            direction='long' if np.random.choice([0, 1]) == 0 else 'short',
            quote_amount=amount * QUOTE_PRECISION, 
            user_index=user_index, 
            market_index=market_index
        )

def collateral_difference(ch, initial_collateral, verbose=False):
    clearing_house = copy.deepcopy(ch)

    # close everyone 
    clearing_house, (chs, events, mark_prices) = close_all_users(clearing_house, verbose)
    
    # recompute collateral 
    end_total_collateral = compute_total_collateral(clearing_house)

    # ensure collateral still adds up 
    abs_difference = abs(initial_collateral - end_total_collateral) 
    
    return abs_difference, events, chs, mark_prices

#%%
seed = np.random.randint(0, 1e3)
# seed = 74
print('seed:', seed)

np.random.seed(seed)
ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
)
market: Market = ch.markets[0]
max_t = len(market.amm.oracle)

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

n_lps = 2
n_trades = 10

# n_lps = 2
# n_trades = 2

sim = RandomSimulation(ch)
agents = []
agents += [
    sim.generate_lp(i, 0) for i in range(n_lps)
]
# agents += [
#     sim.generate_lp_settler(i, 0) for i in range(n_lps)
# ]
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
    event = agent.setup(ch)
    if event._event_name != 'null':
        ch = event.run(ch)
    
    events.append(event)
    clearing_houses.append(copy.deepcopy(ch))
    differences.append(0)
    
    ch.change_time(1)

# record total collateral pre trades     
initial_collateral = compute_total_collateral(ch)

# run agents 
early_exit = False
abs_difference = 0 

for x in tqdm(range(len(market.amm.oracle))):
    if x < ch.time:
        continue
    
    for i, agent in enumerate(agents):
        event_i = agent.run(ch)
        
        if event_i._event_name != 'null':
            ch = event_i.run(ch)
                
            mark_prices.append(calculate_mark_price(market))    
            events.append(event_i)
            clearing_houses.append(copy.deepcopy(ch))

            abs_difference = collateral_difference(ch, initial_collateral, verbose=False)[0]
            differences.append(abs_difference)
    
        if abs_difference > 1:
            early_exit = True 
            break 
                
    if early_exit: 
        break     
    
    ch = ch.change_time(1)

abs_difference, _events, _chs, _mark_prices = collateral_difference(ch, initial_collateral, verbose=True)    
events += _events
clearing_houses += _chs
mark_prices += _mark_prices

differences.append(abs_difference)
abs_difference

#%%
plt.plot([d for d in differences if d != 0])
print(np.unique(differences))

#%%
import matplotlib.colors as mcolors
cmap = mcolors.BASE_COLORS
keys = list(cmap.keys())

mark_change = np.array(mark_prices) - mark_prices[0]
above = True 
plt.plot(mark_change)
for i, e in enumerate(events): 
    if e._event_name != 'null':
        color = cmap[keys[e.user_index % len(keys)]]
        plt.scatter(i, mark_change[i], color=color)
        plt.text(i+0.5, mark_change[i], e._event_name, rotation=90)

#%%
def pprint(x):
    print("\t", x, "\n")

# _ = [pprint(e) for e in events if e._event_name != 'null']
_ = [print(e._event_name, e.user_index) for e in events if e._event_name != 'null']

#%%
_events = [e for e in events if e._event_name != 'null']
print(len(_events))

np.random.seed(seed)
ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
)

init_total_collateral = 0 
for e in _events: 
    ch.time = e.timestamp
    ch = e.run(ch)
    if e._event_name != 'deposit_collateral' and init_total_collateral == 0:
        init_total_collateral = compute_total_collateral(ch)     
    
# recompute collateral 
end_total_collateral = compute_total_collateral(ch)
# ensure collateral still adds up 
abs_difference = abs(init_total_collateral - end_total_collateral)
abs_difference

#%%
#%%
#%%
#%%
#%%
