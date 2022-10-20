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

from sim.helpers import *
from sim.events import * 
from sim.agents import * 

from driftsim.clearing_house.math.pnl import *
from driftsim.clearing_house.math.amm import *
from driftsim.clearing_house.state import *
from driftsim.clearing_house.lib import *

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
    base_asset_reserve=10 * 1e11,
    quote_asset_reserve=10 * 1e11,
    funding_period=2,
    # funding goes to the longs
    peg_multiplier=int((oracle.get_price(0)-1) *1e3), 
    base_asset_amount_step_size=100, 
    minimum_quote_asset_trade_size=100
)
market = SimulationMarket(amm)
fee_structure = FeeStructure(numerator=1, denominator=100)
ch = ClearingHouse([market], fee_structure)

n_users = 3 
init_collateral = 1_0_000 * QUOTE_PRECISION
for i in range(n_users):
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
ch = ch.deposit_user_collateral(1, full_amm_position_quote)

init_collateral = compute_total_collateral(ch)

ch.add_liquidity(
    0, 0, full_amm_position_quote
)

# user goes long (should get paid)
ch.open_position(
   PositionDirection.SHORT, 
   2, 
   init_collateral, 
   0 
)

ch.add_liquidity(
    0, 1, full_amm_position_quote
)

# pay out funding 
ch = ch.change_time(100)
ch = ch.update_funding_rate(0)
# settle user + lps 
ch = ch.settle_funding_rates(2)

market = ch.markets[0]
lp = ch.users[0].positions[0]
metrics = ch.get_lp_metrics(lp, lp.lp_shares, market)
print('lp0 metrics (should get all funding)', metrics)

lp = ch.users[1].positions[0]
metrics = ch.get_lp_metrics(lp, lp.lp_shares, market)
print('lp1 metrics (should get nothing)', metrics)

ch = close_all_users(ch, verbose=True)[0]
end_collateral = compute_total_collateral(ch)
print(init_collateral, end_collateral)

print('done')

# %%
# %%
