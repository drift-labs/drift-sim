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

ch = setup_ch(n_users=3)
market = ch.markets[0]

# from programs.clearing_house.controller.amm import _swap_base_asset
# (new_base_asset_amount,
# new_quote_asset_amount,
# quote_asset_acquired) =  _swap_base_asset(market.amm, 1 * 1e13, SwapDirection.REMOVE)
# print('quote in', quote_asset_acquired)
#
# market.amm.base_asset_reserve = new_base_asset_amount
# market.amm.quote_asset_reserve = new_quote_asset_amount
#
# (new_base_asset_amount,
# new_quote_asset_amount,
# quote_asset_acquired) = _swap_base_asset(market.amm, 1 * 1e13, SwapDirection.ADD)
# print('quote out', quote_asset_acquired)

# compute initial collateral in system 
init_collateral = 0 
init_collaterals = {}
for (i, user) in ch.users.items():
    init_collaterals[i] = user.collateral
    init_collateral += user.collateral 
    print(f'u{i} collateral:', user.collateral)
init_collateral /= 1e6

ch.add_liquidity(0, 0, 1_000_000 * QUOTE_PRECISION)
ch.add_liquidity(0, 1, 1_000_000 * QUOTE_PRECISION)

ch.open_position(    
    PositionDirection.LONG, 
    2, 
    100 * QUOTE_PRECISION,
    0
)

ch.settle_lp(0, 0)
ch.settle_lp(0, 1)

# this settle loses the lp money
og_collateral = ch.users[0].collateral
ch.settle_lp(0, 0)
post_settle_collateral = ch.users[0].collateral

lp_money_lost = og_collateral - post_settle_collateral
print("lp money lost:", lp_money_lost)
print('lp loses money:', post_settle_collateral < og_collateral) # we dont want this

print("close out all the users...")
clearing_house = ch
for market_index in range(len(clearing_house.markets)):
    market: Market = clearing_house.markets[market_index]
    
    for user_index in clearing_house.users:
        user: User = clearing_house.users[user_index]
        position = user.positions[market_index]
        is_lp = position.lp_tokens > 0
        
        if is_lp: 
            event = removeLiquidityEvent(
                clearing_house.time, 
                market_index, 
                user_index,
                position.lp_tokens
            )
            clearing_house = event.run(clearing_house)
            clearing_house = clearing_house.change_time(1)
            print(f"closing lp{user_index}")
        
        if position.base_asset_amount != 0: 
            event = ClosePositionEvent(
                clearing_house.time, 
                user_index, 
                market_index
            )
            clearing_house = event.run(clearing_house)
            clearing_house = clearing_house.change_time(1)
            print(f'closing user{user_index}')

# recompute total collateral in system
final_collateral = 0
for (i, user) in ch.users.items():
    final_collateral += user.collateral
    ui_pnl = user.collateral - init_collaterals[i]
    print(f'u{i} rpnl:', ui_pnl / 1e6)

print("market:", market.amm.total_fee_minus_distributions / 1e6)
final_collateral = final_collateral + market.amm.total_fee_minus_distributions
final_collateral /= 1e6

print("test (init, final):", init_collateral, final_collateral)
print('difference:', init_collateral - final_collateral)

abs_difference = abs(init_collateral - final_collateral) 
print('passes:', abs_difference <= 1e-3)

