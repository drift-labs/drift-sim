# %%
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

from sim.helpers import close_all_users, random_walk_oracle, rand_heterosk_oracle, class_to_json
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

# record total collateral pre trades     
def compute_total_collateral(ch):
    total_collateral = 0 
    init_collaterals = {}
    for (i, user) in ch.users.items():
        init_collaterals[i] = user.collateral
        total_collateral += user.collateral 
    
    for market_index in range(len(ch.markets)):
        market: Market = ch.markets[market_index]
        total_collateral += market.amm.total_fee_minus_distributions

    total_collateral /= 1e6
    return total_collateral

def collateral_difference(ch, initial_collatearl, verbose=False):
    clearing_house = copy.deepcopy(ch)

    # close all the positions
    if verbose: 
        print('closing users..')
    clearing_house, (chs, events, mark_prices) = close_all_users(clearing_house, verbose)
    
    end_total_collateral = compute_total_collateral(clearing_house)
    abs_difference = abs(initial_collatearl - end_total_collateral) 
    
    return abs_difference, events, chs, mark_prices

#%%
ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
    n_users=0,
)

init_events = [
    DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=78096592245, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=1, user_index=1, deposit_amount=680701018549, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=2, user_index=2, deposit_amount=18231000000, username='openclose', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=3, user_index=3, deposit_amount=27479000000, username='openclose', _event_name='deposit_collateral'),
]
for e in init_events: ch = e.run(ch)

total_collateral = compute_total_collateral(ch)

events = [
    addLiquidityEvent(timestamp=227, market_index=0, user_index=0, quote_amount=78096592245, _event_name='add_liquidity'),
    OpenPositionEvent(timestamp=274, user_index=3, direction='short', quote_amount=27479000000, market_index=0, _event_name='open_position'),
    addLiquidityEvent(timestamp=290, market_index=0, user_index=1, quote_amount=680701018549, _event_name='add_liquidity'),
    OpenPositionEvent(timestamp=314, user_index=2, direction='long', quote_amount=18231000000, market_index=0, _event_name='open_position'), 
]

broke = False
_events = []
for e in events: 
    ch = e.run(ch, verbose=True)
    _events.append(e)

    try: 
        abs_difference, close_events, _, _ = collateral_difference(ch, total_collateral)
    except Exception: 
        broke = True 
   
    if abs_difference > 1 or broke:
        print('blahhH!!!')
        break 
   
from pprint import pprint as print
print([e._event_name for e in _events])
    
abs_difference, close_events, _, _ = collateral_difference(ch, total_collateral, verbose=True)
print(close_events)
print(abs_difference)
