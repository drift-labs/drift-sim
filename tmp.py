# %%
%reload_ext autoreload
%autoreload 2

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
from driftpy.math.amm import calculate_price

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.lib import *

from sim.helpers import random_walk_oracle, rand_heterosk_oracle, class_to_json
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
        strategies=strategies,
    )
    market = Market(amm)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    ch = ClearingHouse([market], fee_structure)

    ch = DepositCollateralEvent(
        user_index=0, 
        deposit_amount=1_000 * QUOTE_PRECISION, 
        timestamp=ch.time,
    ).run(ch)

    ch = DepositCollateralEvent(
        user_index=1, 
        deposit_amount=1_000 * QUOTE_PRECISION, 
        timestamp=ch.time,
    ).run(ch)
    
    return ch

"""
user goes long 
user goes closes long 
user pnl = market fees 
"""
ch = setup_ch()

user0: User = ch.users[0]
user1: User = ch.users[1]
market: Market = ch.markets[0]

init_collateral = user0.collateral
ch = ch.open_position(
    PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
).close_position(0, 0)

math.isclose(
    (user0.collateral + market.amm.total_fee_minus_distributions) / 1e6, 
    init_collateral / 1e6
)

#%%
"""
u0 longs 
u1 shorts 
u0 closes (pays pnl to u0) 
u1 closes (pnl from u1) 
"""
ch = setup_ch()

user0: User = ch.users[0]
user1: User = ch.users[1]
market: Market = ch.markets[0]

u0_init_collateral = user0.collateral
u1_init_collateral = user1.collateral
total_collateral = user0.collateral + user1.collateral

total_collateral = user0.collateral + user1.collateral

ch.open_position(
    PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
).open_position(
    PositionDirection.SHORT, 1, 100 * QUOTE_PRECISION, 0
).close_position(
    0, 0
).close_position(
    1, 0
)

u0_pnl_collateral = user0.collateral - u0_init_collateral
u1_pnl_collateral = user1.collateral - u1_init_collateral
print(
    "u0, u1 pnl:",
    u0_pnl_collateral,
    u1_pnl_collateral
)

expected_total_collateral = user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions

math.isclose(total_collateral/1e6, expected_total_collateral/1e6, rel_tol=1e-3)

#%%
"""
u0 longs 
u1 shorts smaller amount [price moves down]
u0 closes (pays pnl to u0) [negative pnl is smaller]
u1 closes (pnl from u1) [positive pnl is smaller]
"""
ch = setup_ch()

user0: User = ch.users[0]
user1: User = ch.users[1]
market: Market = ch.markets[0]

u0_init_collateral = user0.collateral
u1_init_collateral = user1.collateral
total_collateral = user0.collateral + user1.collateral

ch.open_position(
    PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
).open_position(
    PositionDirection.SHORT, 1, 50 * QUOTE_PRECISION, 0
)

print(user0.positions[0])
print(user1.positions[0])

ch = ch.close_position(
    0, 0
).close_position(
    1, 0
)

u0_pnl_collateral = user0.collateral - u0_init_collateral
u1_pnl_collateral = user1.collateral - u1_init_collateral
print(
    "u0, u1, market, pnl:",
    u0_pnl_collateral,
    u1_pnl_collateral, 
    market.amm.total_fee_minus_distributions
)

expected_total_collateral = user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions

math.isclose(total_collateral/1e6, expected_total_collateral/1e6, rel_tol=1e-3)

#%%
#%%
#%%
#%%
"""
lp mints
u0 longs (price goes up)
lp burns (takes on a short pos)
u1 closes 
lp closes 
"""
np.random.seed(0)
ch = setup_ch()

user0: User = ch.users[0]
user1: User = ch.users[1]
market: Market = ch.markets[0]

# percent = 1.
# trade_size = 100_000 

mark_prices = []

# percent = 1 #.5
percent = 100
# trade_size = 1000
trade_size = 100_000 * 1e4
# trade_size = 1_000_000

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6
percent_amm_position_quote = int(full_amm_position_quote * percent)

ch = ch.deposit_user_collateral(
    0, percent_amm_position_quote
).deposit_user_collateral(
    1, trade_size * QUOTE_PRECISION
)

u0_init_collateral = user0.collateral
u1_init_collateral = user1.collateral
total_collateral = user0.collateral + user1.collateral

print('og mark', calculate_mark_price(market))

mark_prices.append(
    calculate_mark_price(market)   
)

print('add liq...')
print(market.amm.sqrt_k, market.amm.net_base_asset_amount)
prev_k = market.amm.sqrt_k
ch = ch.add_liquidity(
    0, 0, percent_amm_position_quote
)
# hardcode
# market.amm.base_asset_reserve *= 2 
# market.amm.quote_asset_reserve *= 2 
# market.amm.sqrt_k = int((
#     market.amm.base_asset_reserve/1e13 * market.amm.quote_asset_reserve/1e13
# ) ** .5) * 1e13

print(market.amm.sqrt_k, market.amm.net_base_asset_amount)

print('opening...')
ch = ch.open_position(
    PositionDirection.LONG, 1, trade_size * QUOTE_PRECISION, 0
)

print('rm liq...')
print(market.amm.sqrt_k, market.amm.net_base_asset_amount)
ch = ch.remove_liquidity(
    0, 0, user0.lp_positions[0].lp_tokens
)
# # hardcode
# market.amm.base_asset_reserve /= 2 
# market.amm.quote_asset_reserve /= 2 
# market.amm.sqrt_k /= 2

print(market.amm.sqrt_k, market.amm.net_base_asset_amount)
print("--- lp:", user0.positions[0])
print("--- user:", user1.positions[0])

mark_prices.append(
    calculate_mark_price(market)   
)

print('postlong mark', calculate_mark_price(market))

# print(
#     "u0, u1, calc upnl:",
#     calculate_position_pnl(market, user0.positions[0]), 
#     calculate_position_pnl(market, user1.positions[0]), 
# )

_lp_position = copy.deepcopy(user0.positions[0])
_user_position = copy.deepcopy(user1.positions[0])

# user close
print('user closes...')
ch = ch.close_position(1, 0)
print('post-user close mark', calculate_mark_price(market))
mark_prices.append(calculate_mark_price(market))

# lp close
print('lp closes...')
ch = ch.close_position(0, 0)
print('post-lp close mark', calculate_mark_price(market))
mark_prices.append(calculate_mark_price(market))

print("lp", user0.positions[0])
print(market.amm.sqrt_k, market.amm.net_base_asset_amount)

u0_pnl_collateral = user0.collateral - u0_init_collateral
u1_pnl_collateral = user1.collateral - u1_init_collateral
print(
    "pnl (u0, u1, market):",
    u0_pnl_collateral / 1e6,
    u1_pnl_collateral / 1e6, 
    market.amm.total_fee_minus_distributions / 1e6
)

expected_total_collateral = user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions
print("test (total, post-sim):", total_collateral/1e6, expected_total_collateral/1e6)
print("difference:", total_collateral/1e6 - expected_total_collateral/1e6)
is_close = math.isclose(total_collateral/1e6, expected_total_collateral/1e6, abs_tol=1e-3)
print('isclose:', is_close)

plt.plot(mark_prices)
# print(abs(mark_prices[0] - mark_prices[-1]) * _lp_position.base_asset_amount / 1e13)
# print(abs(mark_prices[0] - mark_prices[-1]) * _user_position.base_asset_amount / 1e13)
#%%
#%%
#%%
#%%

#%%
#%%
bar, qar = 100, 100 
sqrt_k = np.sqrt(bar * qar)
print(sqrt_k)

# add liq 
add = 1
bar, qar = bar + add, qar + add
sqrt_k = np.sqrt(bar * qar)
print(sqrt_k)

# trade 
tradesize = 10 
bar += tradesize
qar -= tradesize

k = sqrt_k * sqrt_k
bar = bar - add - trade_size
_qar = bar / k
print(_qar, qar - add + tradesize)

# # remove liq
# bar, qar = bar - add - tradesize, qar - add + tradesize
# sqrt_k = np.sqrt(bar * qar)
# bar += tradesize 
# qar -= tradesize

print(sqrt_k)

#%%
#%%
#%%
#%%
#%%
"""
lp mints
u0 longs (price goes up)
lp burns (takes on a short pos)
u1 closes 
lp closes 
"""
np.random.seed(0)
ch = setup_ch()

user0: User = ch.users[0]
user1: User = ch.users[1]
market: Market = ch.markets[0]

print('mark', calculate_mark_price(market))

percent = .5 # LP percentage 
# percent = .5

user_trade_size = 1_000_000
# user_trade_size = 1_000

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6
percent_amm_position_quote = int(full_amm_position_quote * percent)

ch = ch.deposit_user_collateral(
    0, 
    percent_amm_position_quote
).deposit_user_collateral(
    1, 
    user_trade_size * QUOTE_PRECISION
)

total_collateral = 0 
init_collaterals = {}
for (i, user) in ch.users.items():
    init_collaterals[i] = user.collateral
    total_collateral += user.collateral 
    print(f'u{i} collateral:', user.collateral)
total_collateral /= 1e6

ch = ch.add_liquidity(
    0, 0, percent_amm_position_quote
).open_position(
    PositionDirection.LONG, 1, user_trade_size * QUOTE_PRECISION, 0
).remove_liquidity(
    0, 0, user0.lp_positions[0].lp_tokens
)

print()
print(user0)
print()
print('---')
print()
print(user1)
print()
print('---')
print()
print(market.amm.total_fee_minus_distributions)
print()

print(user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions)
print(total_collateral * 1e6)

print(
    "u0, u1, calc upnl:",
    _calculate_position_pnl(ch, market, user0.positions[0]), 
    _calculate_position_pnl(ch, market, user1.positions[0]), 
)

print('---mark', calculate_mark_price(market))
print(
    "u0, u1, calc entry:",
    calculate_entry_price(user0.positions[0]) / 1e10, 
    calculate_entry_price(user1.positions[0]) / 1e10, 
)

ch = ch.close_position(
    1, 0    
).close_position(
    0, 0    
)

current_total_collateral = 0
for (i, user) in ch.users.items():
    ui_pnl = user.collateral - init_collaterals[i]
    current_total_collateral += user.collateral
    print(f'u{i} rpnl:', ui_pnl / 1e6)
print("market:", market.amm.total_fee_minus_distributions / 1e6)
print('mark', calculate_mark_price(market))

expected_total_collateral = current_total_collateral +  + market.amm.total_fee_minus_distributions
expected_total_collateral /= 1e6

abs_difference = abs(total_collateral - expected_total_collateral) 
print("test (total, expected):", total_collateral, expected_total_collateral)
print('difference:', total_collateral - expected_total_collateral)
abs_difference <= 1e-3

#%%

# 100% = full amm position 
# user goes long 
# u take the short 
# user closes (feeds you the pnl)
# lp closes (takes your pnl)

#%%

# 50% = full amm position 
# user goes long 
# u take 50% of the short 
# user closes (feeds you the pnl -- same as before) - really now 50% should go to market 
# lp closes (50% of the pnl)
# where did the other 50% go?

#%%

# 50% = full amm position 
# user goes long 
# u take 50% of the short 
# user closes (feeds you the pnl -- same as before) - really now 50% should go to market 
# lp closes (50% of the pnl)
# where did the other 50% go?

# 50% = full amm position 
# user goes long 
# u take 50% of the short 
# user closes (feeds you the pnl -- same as before) - really now 50% should go to market 
# lp closes (50% of the pnl)
# where did the other 50% go?

#%%
from sim.agents import * 
import numpy as np 

np.random.seed(0)

# ch = setup_ch(
#     base_spread=100, 
#     strategies='PrePeg',
#     n_steps=1_000,
# )

ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
)
clearing_house = ch 
market: Market = ch.markets[0]
max_t = len(market.amm.oracle)

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

n_lps = 1
n_trades = 1

def generate_lp(user_index):
    start = np.random.randint(0, max_t)
    dur = np.random.randint(0, max_t // 2)
    amount = np.random.randint(0, full_amm_position_quote // (n_lps + 10))
    return LP(
        lp_start_time=start,
        lp_duration=dur, 
        deposit_amount=amount, 
        user_index=user_index, 
        market_index=0
    )

def generate_trade(user_index):
    start = np.random.randint(0, max_t)
    dur = np.random.randint(0, max_t // 2)
    amount = np.random.randint(0, 100_000)
    
    return OpenClose(
        start_time=start,
        duration=dur, 
        direction='long' if np.random.choice([0, 1]) == 0 else 'short',
        quote_amount=amount * QUOTE_PRECISION, 
        user_index=user_index, 
        market_index=0
    )

agents = []
# agents += [
#     generate_lp(i) for i in range(n_lps)
# ]
# agents += [
#     generate_trade(i) for i in range(n_lps, n_lps+n_trades)
# ]

agents = [
    LP(
        lp_start_time=0,
        lp_duration=20, 
        deposit_amount=100 * QUOTE_PRECISION, 
        user_index=0, 
        market_index=0
    ),
    OpenClose(
        start_time=10,
        duration=2, 
        direction='long' if np.random.choice([0, 1]) == 0 else 'short',
        quote_amount=100 * QUOTE_PRECISION, 
        user_index=1, 
        market_index=0
    )
]

agents = [
    LP(
        lp_start_time=227,
        lp_duration=105, 
        # deposit_amount=680_701_018549, 
        deposit_amount=full_amm_position_quote, 
        user_index=0, 
        market_index=0
    ),
    OpenClose(
        start_time=314,
        duration=171, 
        direction='long',
        quote_amount=18_231 * 1e6, 
        user_index=1, 
        market_index=0
    )
]

print('#agents:', len(agents))
events = []
clearing_houses = []

# setup agents
for agent in agents:        
    event = agent.setup(ch)
    ch = event.run(ch)
    
    events.append(event)
    clearing_houses.append(copy.deepcopy(ch))
    
    ch.change_time(1)

# record total collateral pre trades     
total_collateral = 0 
init_collaterals = {}
for (i, user) in ch.users.items():
    init_collaterals[i] = user.collateral
    total_collateral += user.collateral 
total_collateral /= 1e6

# run agents 
from tqdm.notebook import tqdm 
for x in tqdm(range(len(market.amm.oracle))):
    if x < clearing_house.time:
        continue
    
    for i, agent in enumerate(agents):
        event_i = agent.run(clearing_house)
        clearing_house = event_i.run(clearing_house)
        
        events.append(event_i)
        clearing_houses.append(copy.deepcopy(clearing_house))
        
    clearing_house = clearing_house.change_time(1)

# close out all the users 
print("close out all the users...")
for market_index in range(len(clearing_house.markets)):
    for user_index in clearing_house.users:
        user: User = clearing_house.users[user_index]
        lp_position: LPPosition = user.lp_positions[market_index]
        market_position: MarketPosition = user.positions[market_index]
        is_lp = lp_position.lp_tokens > 0
        
        if is_lp: 
            clearing_house = clearing_house.remove_liquidity(
                market_index, user_index, lp_position.lp_tokens,
            )
            print(f'u{user_index} rl...')
            
        elif market_position.base_asset_amount != 0: 
            clearing_house = clearing_house.close_position(
                user_index, market_index
            )
            print(f'u{user_index} cp...')
            
        clearing_house = clearing_house.change_time(1)

# ensure collateral still adds up 
current_total_collateral = 0
for (i, user) in ch.users.items():
    ui_pnl = user.collateral - init_collaterals[i]
    current_total_collateral += user.collateral
    print(f'u{i} pnl:', ui_pnl)
print("market:", market.amm.total_fee_minus_distributions)

expected_total_collateral = current_total_collateral + market.amm.total_fee_minus_distributions
expected_total_collateral /= 1e6

abs_difference = abs(total_collateral - expected_total_collateral) 
print("test (total, expected):", total_collateral, expected_total_collateral)
print('difference:', abs_difference)
abs_difference <= 1e-3

#%%
fevents = [e for e in events if e._event_name != 'null']
fevents

#%%
#%%
#%%
#%%
#%%
#%%
#%%
#%%
#%%