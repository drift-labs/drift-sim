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

from driftsim.clearing_house.math.pnl import *
from driftsim.clearing_house.math.amm import *
from driftsim.clearing_house.state import *
from driftsim.clearing_house.lib import *

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

amm = SimulationAMM(
    oracle=oracle, 
    base_asset_reserve=1_000_000 * 1e13,
    quote_asset_reserve=1_000_000 * 1e13,
    funding_period=2,
    peg_multiplier=int(oracle.get_price(0)*1e3), 
    base_spread=100, 
    base_asset_amount_step_size=0, 
    minimum_quote_asset_trade_size=0,
)
market = SimulationMarket(amm)
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
full_amm_position_quote -= 100 * 1e6

ch = DepositCollateralEvent(
    user_index=1, 
    deposit_amount=full_amm_position_quote, 
    timestamp=ch.time,
).run(ch)

from sim.helpers import compute_total_collateral, close_all_users

init_collateral = compute_total_collateral(ch)

# ch.add_liquidity(
#     0, 1, full_amm_position_quote
# )

# user goes long (should get paid)
ch.open_position(
   PositionDirection.LONG, 
   0, 
   100 * QUOTE_PRECISION, 
   0 
)

ch.open_position(
   PositionDirection.SHORT, 
   1, 
   100 * QUOTE_PRECISION, 
   0 
)

# # user goes short
# ch.close_position(
#    0, 
#    0 
# )

print()
# trader: MarketPosition = ch.users[0].positions[0]
# print(
#     'trader pos', 
#     trader.base_asset_amount, 
#     trader.quote_asset_amount
# )

# lp: MarketPosition = ch.users[1].positions[0]
# ratio = lp.lp_shares / market.amm.sqrt_k
# market = ch.markets[0]
# metrics = ch.get_lp_metrics(lp, lp.lp_shares, market)
# print(
#     "lp pos", 
#     metrics.base_asset_amount / ratio, 
#     metrics.quote_asset_amount / ratio
# )

#%%
#%%
#%%
print(market.amm.total_fee_minus_distributions)

ch = close_all_users(ch)[0]
end_collateral = compute_total_collateral(ch)

print(init_collateral, end_collateral)
print('difference', init_collateral - end_collateral)

print('done')
# print(ch.to_json())

# %%
# %%
