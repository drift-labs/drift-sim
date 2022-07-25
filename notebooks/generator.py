#%%
%load_ext autoreload
%autoreload 2

import sys 

sys.path.insert(0, 'driftpy/src/')

import driftpy

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction
)
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PEG_PRECISION
from driftpy.math.amm import calculate_price

from dataclasses import dataclass, field

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from driftpy.constants.numeric_constants import *

from state import * 
from events import *
from helpers import random_walk_oracle

import unittest

#%%
def setup():
    ## or can load from a csv file
    prices, timestamps = random_walk_oracle(1)
    oracle = Oracle(prices=prices, timestamps=timestamps)

    amm = AMM(
        oracle=oracle, 
        base_asset_reserve=100_000 * AMM_RESERVE_PRECISION, 
        quote_asset_reserve=100_000 * AMM_RESERVE_PRECISION,
        funding_period=60, 
        peg_multiplier=1 * PEG_PRECISION
    )
    market = Market(amm)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    clearing_house = ClearingHouse([market], fee_structure)

    return clearing_house

#%%
## generate a few random trades 
events = [] 
time = 0 

# initialize user 
event = DepositCollateralEvent(
    user_index=0, 
    deposit_amount=1_000 * QUOTE_PRECISION, 
    timestamp=time, 
)
events.append(event)
time += 1 

# do some trades 
for _ in range(1):
    r = np.random.randint(low=0, high=10_000)
    
    event = OpenPositionEvent(
        user_index=0, 
        direction="long" if r % 2 == 0 else "short",
        quote_amount=r % 1_000, 
        timestamp=time, 
        market_index=0, 
    )    
    events.append(event)
    
    time += r % 20 

## put them in a csv + save it 
rows = [e.serialize_to_row() for e in events]
print(len(rows))
simulation_df = pd.DataFrame.from_dict(rows)
simulation_df.to_csv("sim.csv", index=False)

# %%
clearing_house = setup()

event_types: list[Event] = [
    DepositCollateralEvent,
    OpenPositionEvent, 
]

for i, event_row in simulation_df.iterrows():     
    for event_type in event_types:
        if event_row.event_name == event_type._event_name: 
            print(f'running {event_type._event_name}...')
            Event.run_row(event_type, clearing_house, event_row)

# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
# %%
#### --- graveyard --- 

# # clearing house state0 
# # deposit collateral for user event0
# # user goes long event1 
# # clearing house state1 

# #%%
# clearing_house = clearing_house.add_user(0, 1_000 * QUOTE_PRECISION)

# #%%
# clearing_house = clearing_house.open_position(
#     PositionDirection.LONG, 
#     0, 
#     100 * QUOTE_PRECISION,
#     0
# )

# #%%
# clearing_house.to_json()

# #%%
# clearing_house.add_user(1, 1_000 * QUOTE_PRECISION)

# print(calculate_mark_price(market))

# clearing_house.open_position(
#     PositionDirection.LONG, 
#     0, 
#     100 * QUOTE_PRECISION, 
#     0
# )

# print(calculate_mark_price(market))

# clearing_house.open_position(
#     PositionDirection.LONG, 
#     1, 
#     1000 * QUOTE_PRECISION * 20, 
#     0
# )

# print(calculate_mark_price(market))

# # clearing_house.users[0], clearing_house.users[1]

# driftpy.math.positions.calculate_base_asset_value(
#     market, 
#     clearing_house.users[0].positions[0]
# )

# # %%
# base_v = driftpy.math.positions.calculate_base_asset_value(
#     market, 
#     clearing_house.users[0].positions[0]
# ) 
# pnl = driftpy.math.positions.calculate_position_pnl(
#     market, 
#     clearing_house.users[0].positions[0]
# )

# base_v, pnl

# # %%
# # %%
# simulation_df = pd.read_csv("sim.csv")
# simulation_df.head()

# users = []
# # initialize users 
# for i, event_row in simulation_df.iterrows():     
#     if event_row.event_name == OpenPositionEvent._event_name: 
#         trade_event = Event.deserialize_from_row(
#             OpenPositionEvent, 
#             event_row
#         )  
#         user_index = trade_event.user_index
              
#         if user_index not in users: 
#             print(f"adding {user_index}")
#             clearing_house.add_user(user_index, 1_000_000)
#             users.append(user_index)

# # %%
# pos = []
# collat = []
# fee = []

# event_types = [
#     OpenPositionEvent
# ]
# for i, event_row in simulation_df.iterrows():     
#     for event_type in event_types:
#         if event_row.event_name == event_type._event_name: 
            
#             pos.append(clearing_house.users[0].positions[0].base_asset_amount)
#             collat.append(clearing_house.users[0].collateral_amount)
#             fee.append(clearing_house.markets[0].total_fees)
   
#             event_type.run(clearing_house, event_row)
            
# plt.plot(pos)
# plt.show()
# plt.plot(collat)
# plt.show()
# plt.plot(fee)
# plt.show()         

# #%%
# te = OpenPositionEvent(
#     user_index=0, 
#     direction="long",
#     quote_amount=100, 
#     timestamp=0,
#     market_index=0,
# )
# te.serialize_to_row()