# %%
import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, './driftpy/src/')
sys.path.insert(0, '../driftpy/src/')
sys.path.insert(0, '../')

import os 
import datetime
import math 

import driftpy
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
from driftpy.math.amm import calculate_price

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.lib import *

from sim.helpers import random_walk_oracle, rand_heterosk_oracle, class_to_json
from sim.events import * 
from sim.agents import * 

np.random.seed(0)

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
            deposit_amount=1_000_000 * QUOTE_PRECISION, 
            timestamp=ch.time,
        ).run(ch)

    return ch

ch = setup_ch(n_users=2)

market = ch.markets[0]
market.amm.total_fee_minus_distributions = 0 

ch.add_liquidity(0, 0, 1_000_000 * QUOTE_PRECISION)
ch.add_liquidity(0, 1, 1_000_000 * QUOTE_PRECISION)

market.amm.total_fee_minus_distributions = 100 

ch.settle_lp(0, 0)
print(market.amm.total_fee_minus_distributions)
ch.settle_lp(0, 1)
print(market.amm.total_fee_minus_distributions)

print(
    "market_fee, user_fee:",
    market.amm.total_fee_minus_distributions, 
    ch.users[0].positions[0].last_total_fee_minus_distributions,
)
og_collateral = ch.users[0].collateral
ch.settle_lp(0, 0)
post_settle_collateral = ch.users[0].collateral

print('lp loses money:', post_settle_collateral < og_collateral)


