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

from sim.helpers import *

from driftsim.clearing_house.math.pnl import *
from driftsim.clearing_house.math.amm import *
from driftsim.clearing_house.state import *
from driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 

def setup_ch(base_spread=0, strategies='', n_steps=100):
    prices, timestamps = random_walk_oracle(1, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=1_000_000 * 1e13,
        quote_asset_reserve=1_000_000 * 1e13,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*1e3),
        base_spread=base_spread,
        strategies=strategies
    )
    market = SimulationMarket(amm)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    ch = ClearingHouse([market], fee_structure)

    return ch

#%%
seed = 85
np.random.seed(seed)
print('seed', seed)
ch = setup_ch(
    n_steps=100,
    base_spread=0,
)
market = ch.markets[0]

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

trade_size = 1_000_000 * QUOTE_PRECISION
events = [
    DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=1998590197697, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=1, user_index=1, deposit_amount=4255468411490, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=4, user_index=2, deposit_amount=79010000000, username='openclose', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=5, user_index=3, deposit_amount=1802000000, username='openclose', _event_name='deposit_collateral'),

    addLiquidityEvent(timestamp=142, market_index=0, user_index=1, quote_amount=4255468411490, _event_name='add_liquidity'),
    SettleLPEvent(timestamp=183, user_index=1, market_index=0, _event_name='settle_lp'),
    OpenPositionEvent(timestamp=227, user_index=2, direction='long', quote_amount=79010000000, market_index=0, _event_name='open_position'),

    removeLiquidityEvent(timestamp=10000000000227.0, market_index=0, user_index=1, lp_token_amount=-1, _event_name='remove_liquidity'),
    ClosePositionEvent(timestamp=10000000000228.0, user_index=1, market_index=0, _event_name='close_position'),
    ClosePositionEvent(timestamp=10000000000229.0, user_index=2, market_index=0, _event_name='close_position'),
]

init_total_collateral = 0
broke = False
_events = []
for e in events: 
    if e._event_name != 'deposit_collateral' and init_total_collateral == 0:
        init_total_collateral = compute_total_collateral(ch)

    ch.time = e.timestamp 
    ch = e.run(ch, verbose=True)
    _events.append(e)    

    if init_total_collateral == 0: continue
   
print([e._event_name for e in _events])

abs_difference, close_events, _chs, _ = collateral_difference(ch, init_total_collateral, verbose=True)
market = ch.markets[0]

print(close_events)
print('---')
print("final abs diff:", abs_difference)
net_baa = market.amm.base_asset_amount_with_amm # should be zero ?
net_baa_lp = market.amm.cumulative_base_asset_amount_with_amm_per_lp
print('net baa', net_baa)
print('---')

# %%
lp_fee_payments = 0 
market_fees = 0 
market: SimulationMarket = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_fee_payments += position.lp_fee_payments
    market_fees += position.market_fee_payments

total_payments = lp_fee_payments + market.amm.total_fee_minus_distributions
print(abs(total_payments) - abs(market_fees))

# %%
lp_funding_payments = 0 
market_funding = 0 
market: SimulationMarket = ch.markets[0]
for (_, user) in ch.users.items(): 
    position: MarketPosition = user.positions[0]
    lp_funding_payments += position.lp_funding_payments
    market_funding += position.market_funding_payments
total_payments = market.amm.lp_funding_payment + lp_funding_payments
market_funding + total_payments

# %%
# # %%
# %%
# %%
