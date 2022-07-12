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

prices = [2] * 20
timestamps = np.arange(len(prices))
oracle = Oracle(prices=prices, timestamps=timestamps)

amm = AMM(
    oracle=oracle, 
    base_asset_reserve=1_000_000 * 1e13,
    quote_asset_reserve=1_000_000 * 1e13,
    funding_period=2,
    peg_multiplier=int(oracle.get_price(0)+2*1e3), # funding goes to longs
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

#%%
np.random.seed(74)

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

ch = DepositCollateralEvent(
    user_index=1, 
    deposit_amount=full_amm_position_quote, 
    timestamp=ch.time,
).run(ch)

ch.add_liquidity(
    0, 1, full_amm_position_quote
)

ch.open_position(
   PositionDirection.LONG, 
   0, 100 * QUOTE_PRECISION, 0
)
ch.change_time(5)

ch.update_funding_rate(0)
ch.settle_funding_rates(0)

lp_share = ch.users[1].positions[0].lp_tokens / ch.markets[0].amm.sqrt_k
print('lp share', lp_share)

ch.remove_liquidity(
    0, 1
)

print('done')


# %%
# %%
