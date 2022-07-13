# %%
%reload_ext autoreload
%autoreload 
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

from sim.helpers import close_all_users, random_walk_oracle, compute_total_collateral
from sim.events import * 
from sim.agents import * 

def setup_ch(base_spread=0, strategies='', n_steps=100):
    prices, timestamps = random_walk_oracle(1, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = AMM(
        oracle=oracle, 
        base_asset_reserve=1_000_000 * 1e13,
        quote_asset_reserve=1_000_000 * 1e13,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*1e3),
        base_spread=base_spread,
        strategies=strategies
    )
    market = Market(amm)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    ch = ClearingHouse([market], fee_structure)

    return ch

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
seed = 912
np.random.seed(seed)
ch = setup_ch(
    base_spread=0,
    n_steps=100,
)

events = [
    DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=2264545145255, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=14, user_index=14, deposit_amount=97722000000, username='openclose', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=4, user_index=4, deposit_amount=1596254751582, username='LP', _event_name='deposit_collateral'),
    
    addLiquidityEvent(timestamp=32, market_index=0, user_index=0, quote_amount=2264545145255, _event_name='add_liquidity'),
    OpenPositionEvent(timestamp=44, user_index=14, direction='long', quote_amount=97722000000, market_index=0, _event_name='open_position'),
    addLiquidityEvent(timestamp=69, market_index=0, user_index=4, quote_amount=1596254751582, _event_name='add_liquidity'),
    
    # removeLiquidityEvent(timestamp=69, market_index=0, user_index=0, lp_token_amount=548024090134795008, _event_name='remove_liquidity'),
    # ClosePositionEvent(timestamp=70, user_index=0, market_index=0, _event_name='close_position'),
    # removeLiquidityEvent(timestamp=71, market_index=0, user_index=4, lp_token_amount=386296585736895552, _event_name='remove_liquidity'),
    # ClosePositionEvent(timestamp=72, user_index=14, market_index=0, _event_name='close_position'),
]

init_total_collateral = 0
broke = False
_events = []
for e in events: 
    if e._event_name != 'deposit_collateral' and init_total_collateral == 0:
        init_total_collateral = compute_total_collateral(ch)

    # ch.time = e.timestamp 
    ch = e.run(ch, verbose=True)
    _events.append(e)    

    if init_total_collateral == 0: continue

    try: 
        abs_difference, close_events, _, _ = collateral_difference(ch, init_total_collateral)
    except Exception as e: 
        abs_difference = 0
        broke = True 
        print(e)
   
    if abs_difference > 1 or broke:
        print("abs diff:", abs_difference)
        print('blahhH!!!')
        break 
   
print([e._event_name for e in _events])

abs_difference, close_events, _chs, _ = collateral_difference(ch, init_total_collateral, verbose=True)
ch = _chs[-1]
print(close_events)
print(abs_difference)

# %%


# %%
# %%
# %%
lp_fee_payments = 0 
market_fees = 0 
market: Market = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_fee_payments += position.lp_fee_payments
    market_fees += position.market_fee_payments

total_payments = lp_fee_payments + market.amm.total_fee_minus_distributions
print(total_payments, market_fees)
print(abs(total_payments) - abs(market_fees))

# %%
lp_funding_payments = 0 
market_funding = 0 
market: Market = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_funding_payments += position.lp_funding_payments
    market_funding += position.market_funding_payments
total_payments = market.amm.upnl + lp_funding_payments
market_funding + total_payments

# %%


# %%
# %%
# %%
# %%
np.random.seed(74)
ch = setup_ch(
    base_spread=0,
    n_steps=100,
)

init_events = [
    DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=518187136446, username='LP', _event_name='deposit_collateral'), 
    DepositCollateralEvent(timestamp=1, user_index=1, deposit_amount=969304333976, username='LP', _event_name='deposit_collateral'), 
    DepositCollateralEvent(timestamp=2, user_index=2, deposit_amount=21850000000, username='openclose', _event_name='deposit_collateral'), 
]
for e in init_events: ch = e.run(ch)
total_collateral = compute_total_collateral(ch)

init_ch = copy.deepcopy(ch).to_json()

events = [
    OpenPositionEvent(timestamp=236, user_index=2, direction='short', quote_amount=21850000000, market_index=0, _event_name='open_position'), 

    # addLiquidityEvent(timestamp=353, market_index=0, user_index=1, quote_amount=969304333976, _event_name='add_liquidity'), 
    addLiquidityEvent(timestamp=353, market_index=0, user_index=1, quote_amount=518187136446, _event_name='add_liquidity'), 
    addLiquidityEvent(timestamp=381, market_index=0, user_index=0, quote_amount=518187136446, _event_name='add_liquidity'), 
    
    ClosePositionEvent(timestamp=481, user_index=2, market_index=0, _event_name='close_position'), 

    removeLiquidityEvent(timestamp=513, market_index=0, user_index=0, lp_token_amount=-1, _event_name='remove_liquidity'), 
    ClosePositionEvent(timestamp=518, user_index=0, market_index=0, _event_name='close_position'), 
    
    removeLiquidityEvent(timestamp=519, market_index=0, user_index=1, lp_token_amount=-1, _event_name='remove_liquidity'), 
    ClosePositionEvent(timestamp=520, user_index=1, market_index=0, _event_name='close_position'), 
]

for e in events: 
    ch = e.run(ch, verbose=True)

end_ch = copy.deepcopy(ch).to_json()

compute_total_collateral(ch), total_collateral, compute_total_collateral(ch) - total_collateral

# %%
for k in init_ch.keys(): 
    if type(init_ch[k]) in [int, float]:
        diff = end_ch[k] - init_ch[k]
        if abs(diff) > 0: 
            print(k, diff)

# %%


