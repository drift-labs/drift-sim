# NOTE: i used print statements for the LP and traders funding payments and made sure they added up

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

from sim.helpers import close_all_users, random_walk_oracle, compute_total_collateral
from sim.events import * 
from sim.agents import * 

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
prices = [2] * 20
timestamps = np.arange(len(prices))
oracle = Oracle(prices=prices, timestamps=timestamps)

amm = AMM(
    oracle=oracle, 
    base_asset_reserve=1_000_000 * 1e13,
    quote_asset_reserve=1_000_000 * 1e13,
    funding_period=2,
    peg_multiplier=int(oracle.get_price(0) * 1e3), # funding goes to longs
    minimum_base_asset_trade_size=10, 
    minimum_quote_asset_trade_size=10,
)
market = Market(amm)
fee_structure = FeeStructure(numerator=1, denominator=100)
ch = ClearingHouse([market], fee_structure)

init_collateral = 1_000 * QUOTE_PRECISION
for i in range(2):
    ch = DepositCollateralEvent(
        user_index=i, 
        deposit_amount=init_collateral, 
        timestamp=ch.time,
    ).run(ch)

np.random.seed(74)

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

ch = ch.deposit_user_collateral(0, full_amm_position_quote)

init_collateral = compute_total_collateral(ch)
ch = ch.add_liquidity(0, 0, full_amm_position_quote)

# user goes long (should get paid)
ch.open_position(
   PositionDirection.LONG, 
   1, 
   50 * QUOTE_PRECISION, 
   0 
)
lp = ch.users[0].positions[0]
tokens = lp.lp_shares

# lp goes long 
ch.open_position(
   PositionDirection.LONG, 
   0, 
   50 * QUOTE_PRECISION, 
   0 
)
ch.settle_lp(0, 0)
lp = ch.users[0].positions[0]
print(lp.base_asset_amount, lp.quote_asset_amount, lp.lp_base_asset_amount, lp.lp_quote_asset_amount)
user = ch.users[1].positions[0]
print(user.base_asset_amount, user.quote_asset_amount)

# should close both lp position and market position 
ch.close_position(0, 0)
print(lp)

ch = close_all_users(ch)[0]
end_collateral = compute_total_collateral(ch)
print('collateral diff', init_collateral - end_collateral)
market = ch.markets[0]
print(market.amm.net_base_asset_amount)

print("long diff", market.amm.quote_asset_amount_long, market.base_asset_amount_long)
print("short diff", market.amm.quote_asset_amount_short, market.base_asset_amount_short)

print(market.open_interest)

print('done')
# print(ch.to_json())

# %%
# %%
