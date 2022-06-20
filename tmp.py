# %%
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
# trade_size = 100_000 * 1e4
trade_size = 1_000_000

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

# lp close
print('lp closes...')
ch = ch.close_position(0, 0)
print('post-lp close mark', calculate_mark_price(market))
mark_prices.append(calculate_mark_price(market))

# user close
print('user closes...')
ch = ch.close_position(1, 0)
print('post-user close mark', calculate_mark_price(market))
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
ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
    n_users=0,
)
init_collateral = 100 * QUOTE_PRECISION
market = ch.markets[0]
print('ar', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)

ch = ch.deposit_user_collateral(
    user_index=0, 
    collateral_amount=100 * QUOTE_PRECISION
).open_position(
    PositionDirection.LONG, 
    0, 100 * QUOTE_PRECISION, 0
).close_position(
    0, 0
)

print('ar', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)
# ch.users[0].collateral + ch.markets[0].amm.total_fee_minus_distributions, init_collateral

#%%
#%%
#%%
# compute swap output 
ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
    n_users=0,
)
market = ch.markets[0]
print('ar', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)

market: Market = ch.markets[0]
direction = PositionDirection.LONG
swap_direction = {
    PositionDirection.SHORT: SwapDirection.REMOVE,
    PositionDirection.LONG: SwapDirection.ADD
}[direction]

initial_base_asset_amount = market.amm.base_asset_reserve
initial_quote_asset_amount = market.amm.quote_asset_reserve

[new_quote_asset_amount, new_base_asset_amount] = driftpy.math.positions.calculate_amm_reserves_after_swap(
    market.amm, 
    driftpy.math.amm.AssetType.QUOTE,
    1 * QUOTE_PRECISION, 
    swap_direction,
)
# update market 
market.amm.base_asset_reserve = new_base_asset_amount
market.amm.quote_asset_reserve = new_quote_asset_amount
print('ar', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)

assert initial_quote_asset_amount < new_quote_asset_amount
assert initial_base_asset_amount > new_base_asset_amount

base_amount_acquired = initial_base_asset_amount - new_base_asset_amount
print("base:", base_amount_acquired / 1e13)
# print('ar', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)

initial_quote_asset_reserve = market.amm.quote_asset_reserve
swap_direction = {
    PositionDirection.SHORT: SwapDirection.REMOVE,
    PositionDirection.LONG: SwapDirection.ADD
}[direction]

initial_base_asset_amount = market.amm.base_asset_reserve
initial_quote_asset_amount = market.amm.quote_asset_reserve

[new_quote_asset_amount, new_base_asset_amount] = driftpy.math.positions.calculate_amm_reserves_after_swap(
    market.amm, 
    driftpy.math.amm.AssetType.BASE,
    base_amount_acquired, 
    SwapDirection.ADD,
)

# update market 
# market.amm.base_asset_reserve = new_base_asset_amount
# market.amm.quote_asset_reserve = new_quote_asset_amount
print('ar', new_base_asset_amount, new_quote_asset_amount)

assert initial_quote_asset_amount > new_quote_asset_amount
assert initial_base_asset_amount < new_base_asset_amount

#%%
#%%
quote_reserve_change = {
    SwapDirection.ADD: initial_quote_asset_reserve - new_quote_asset_amount,
    SwapDirection.REMOVE: new_quote_asset_amount - initial_quote_asset_reserve,
}[swap_direction]

# reserves to quote amount 
quote_amount_acquired = (
    quote_reserve_change 
    * market.amm.peg_multiplier 
    / AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO
)
print("quote:", quote_amount_acquired / 1e6)

#%%
#%%
#%%
#%%
#%%
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
    n_users=0,
)
clearing_house = ch 
market: Market = ch.markets[0]
max_t = len(market.amm.oracle)

peg = market.amm.peg_multiplier / PEG_PRECISION
sqrt_k = market.amm.sqrt_k / 1e13
full_amm_position_quote = sqrt_k * peg * 2 * 1e6

n_lps = 4
n_trades = 20

# n_lps = 2
# n_trades = 2

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
agents += [
    generate_lp(i) for i in range(n_lps)
]
agents += [
    generate_trade(i) for i in range(n_lps, n_lps+n_trades)
]

def collateral_difference(ch, initial_collatearl, verbose=False):
    clearing_house = copy.deepcopy(ch)
    
    events = []
    clearing_houses = []
    mark_prices = []
        
    # close out all the users 
    # print("close out all the users...")
    for market_index in range(len(clearing_house.markets)):
        market: Market = clearing_house.markets[market_index]
        
        for user_index in clearing_house.users:
            user: User = clearing_house.users[user_index]
            lp_position: LPPosition = user.lp_positions[market_index]
            is_lp = lp_position.lp_tokens > 0
            
            if is_lp: 
                event = removeLiquidityEvent(
                    clearing_house.time, 
                    market_index, 
                    user_index,
                    lp_position.lp_tokens
                )
                clearing_house = event.run(clearing_house)
                
                mark_prices.append(calculate_mark_price(market))
                events.append(event)
                clearing_houses.append(copy.deepcopy(clearing_house))
            
                if verbose: 
                    print(f'u{user_index} rl...')
                clearing_house = clearing_house.change_time(1)
            
            user: User = clearing_house.users[user_index]
            market_position: MarketPosition = user.positions[market_index]
            if market_position.base_asset_amount != 0: 
                event = ClosePositionEvent(
                    clearing_house.time, 
                    user_index, 
                    market_index
                )
                clearing_house = event.run(clearing_house)
                
                mark_prices.append(calculate_mark_price(market))
                events.append(event)
                clearing_houses.append(copy.deepcopy(clearing_house))
                
                if verbose: 
                    print(f'u{user_index} cp...')
                clearing_house = clearing_house.change_time(1)

    # ensure collateral still adds up 
    current_total_collateral = 0
    total_funding_payments = 0 
    for (i, user) in clearing_house.users.items():
        ui_pnl = user.collateral - init_collaterals[i]
        current_total_collateral += user.collateral
        total_funding_payments += user.total_funding_payments
    #     print(f'u{i} ({clearing_house.usernames[i]}) pnl:', ui_pnl)
    # print("market:", market.amm.total_fee_minus_distributions)

    end_total_collateral = current_total_collateral + market.amm.total_fee_minus_distributions
    end_total_collateral /= 1e6

    abs_difference = abs(initial_collatearl - end_total_collateral) 
    # print("test (total, end):", initial_collatearl, end_total_collateral)
    # print('difference:', abs_difference)
    abs_difference <= 1e-3
    
    return abs_difference, events, clearing_houses, mark_prices

print('#agents:', len(agents))

mark_prices = []
events = []
clearing_houses = []
differences = []

# setup agents
for agent in agents:        
    event = agent.setup(ch)
    ch = event.run(ch)
    
    # events.append(event)
    # clearing_houses.append(copy.deepcopy(ch))
    # differences.append(0)
    
    ch.change_time(1)

# record total collateral pre trades     
total_collateral = 0 
init_collaterals = {}
for (i, user) in ch.users.items():
    init_collaterals[i] = user.collateral
    total_collateral += user.collateral 
total_collateral /= 1e6

# run agents 
early_exit = False

from tqdm.notebook import tqdm 
for x in tqdm(range(len(market.amm.oracle))):
# for x in tqdm(range(130)):
    if x < clearing_house.time:
        continue
    
    for i, agent in enumerate(agents):
        event_i = agent.run(clearing_house)
        clearing_house = event_i.run(clearing_house)
                
        mark_prices.append(
            calculate_mark_price(market)   
        )
        
        abs_difference = collateral_difference(clearing_house, total_collateral, verbose=False)[0]
        differences.append(
            abs_difference
        )
        
        events.append(event_i)
        clearing_houses.append(copy.deepcopy(clearing_house))
        
        if abs_difference > 1:
            early_exit = True 
            break 
    
    if early_exit: 
        break     
    
    clearing_house = clearing_house.change_time(1)

abs_difference, _events, _clearing_houses, _mark_prices = collateral_difference(clearing_house, total_collateral, verbose=True)    
events += _events
clearing_houses += _clearing_houses
mark_prices += _mark_prices

differences.append(
    abs_difference
)
abs_difference

#%%
plt.plot(differences)

#%%
import matplotlib.colors as mcolors
cmap = mcolors.BASE_COLORS
keys = list(cmap.keys())

mark_change = np.array(mark_prices) - mark_prices[0]
above = True 
plt.plot(mark_change)
for i, e in enumerate(events): 
    if e._event_name != 'null':
        color = cmap[keys[e.user_index % len(keys)]]
        plt.scatter(i, mark_change[i], color=color)
        plt.text(i+0.5, mark_change[i], e._event_name, rotation=90)

#%%
def pprint(x):
    print("\t", x, "\n")

# _ = [[i, pprint(events[i]), pprint(clearing_houses[i].to_json()), pprint(differences[i])] for i in range(len(events)) if events[i]._event_name != 'null' or differences[i+1] > 0]

_ = [print("\t", e, "\n") for e in events if e._event_name != 'null']

#%%
good = {'m0_mark_price': 6.334801526388191, 'm0_oracle_price': 20.80728147496417, 'm0_bid_price': 6.334801526388191, 'm0_ask_price': 6.334801526388191, 'm0_wouldbe_peg': 6.355, 'm0_wouldbe_peg_cost': 0.0, 'm0_predicted_long_funding': -0.00022218977311345997, 'm0_predicted_short_funding': -0.00022218977311345997, 'm0_last_mid_price_twap': 6.318663332965472, 'm0_repeg_to_oracle_cost': -21017.554509601236, 'm0_market_index': 0, 'm0_base_asset_amount_long': 2.885736343763763e+16, 'm0_base_asset_amount_short': -4.34265982565888e+16, 'm0_base_asset_amount': -1.4569234818951168e+16, 'm0_total_base_asset_amount': 0, 'm0_open_interest': 2, 'm0_total_exchange_fees': 0.0, 'm0_total_mm_fees': 0.0, 'm0_margin_ratio_initial': 1000, 'm0_margin_ratio_maintenance': 625, 'm0_margin_ratio_partial': 500, 'm0_base_asset_reserve': '10552346270870548480', 'm0_quote_asset_reserve': '10518807122531469312', 'm0_funding_period': 60, 'm0_sqrt_k': 1.053556335054996e+19, 'm0_peg_multiplier': 6355, 'm0_total_lp_tokens': 1.053556335054996e+19, 'm0_lp_tokens': 1.0061444997832415e+19, 'm0_cumulative_lp_funding': -321356827098757.1, 'm0_last_funding_rate': -74, 'm0_last_funding_rate_ts': 274, 'm0_cumulative_funding_rate_long': -74, 'm0_cumulative_funding_rate_short': -74, 'm0_last_oracle_price': 18.67176461391388, 'm0_last_oracle_conf': 0, 'm0_last_oracle_normalised_price': 6.355578474019053, 'm0_last_oracle_price_twap': 13.537084903264308, 'm0_last_oracle_price_twap_ts': 314, 'm0_last_mark_price': 0, 'm0_last_mark_price_twap': 6.318360527406851, 'm0_last_bid_price_twap': 6.318663332965472, 'm0_last_ask_price_twap': 6.318663332965472, 'm0_last_mark_price_twap_ts': 314, 'm0_net_base_asset_amount': -1.4569234818951168e+16, 'm0_net_quote_asset_amount': -45710000000, 'm0_base_spread': 0, 'm0_mark_std': 0.0, 'm0_buy_intensity': 0, 'm0_sell_intensity': 0, 'm0_last_spread': 0, 'm0_bid_price_before': 6.300494999448206, 'm0_ask_price_before': 6.300494999448206, 'm0_total_fee': 457.1, 'm0_total_fee_minus_distributions': 454.6359147887497, 'm0_strategies': '', 'm0_minimum_quote_asset_trade_size': 10000000, 'm0_quote_asset_amount_long': 18231000000, 'm0_quote_asset_amount_short': 27479000000, 'm0_terminal_quote_asset_reserve': 1e+19, 'LP0_collateral': 78099056330.21126, 'LP0_free_collateral': 78093630917.34776, 'LP0_margin_ratio': 1459.405031191314, 'LP0_total_position_value': 53514261.41085491, 'LP0_total_fee_paid': 0, 'LP0_total_fee_rebate': 0, 'LP0_open_orders': 0, 'LP0_cumulative_deposits': 78096592245, 'LP0_m0_base_asset_amount': 84477295142176.45, 'LP0_m0_quote_asset_amount': 53588248.13326977, 'LP0_m0_last_cumulative_funding_rate': -74, 'LP0_m0_last_funding_rate_ts': 332, 'LP0_m0_upnl': -73986.72241485864, 'LP0_m0_upnl_noslip': -53588194.618579954, 'LP0_m0_ufunding': 0.0, 'LP0_total_collateral': 78098982343.48885, 'LP1_collateral': 680701018549, 'LP1_free_collateral': 680701018549, 'LP1_margin_ratio': 'nan', 'LP1_total_position_value': 0, 'LP1_total_fee_paid': 0, 'LP1_total_fee_rebate': 0, 'LP1_open_orders': 0, 'LP1_cumulative_deposits': 680701018549, 'LP1_m0_lp_tokens': 535563350549960640, 'LP1_m0_last_total_fee_minus_distributions': 274790000.0, 'LP1_m0_last_cumulative_lp_funding': -321356827098757.1, 'LP1_m0_last_net_base_asset_amount': -4.34265982565888e+16, 'LP1_m0_last_quote_asset_reserve': 1.0551466747987866e+19, 'LP1_total_collateral': 680701018549, 'openclose2_collateral': 18048690000.0, 'openclose2_free_collateral': 16225330535.565382, 'openclose2_margin_ratio': 0.9899998418636524, 'openclose2_total_position_value': 18230711706.183758, 'openclose2_total_fee_paid': 182310000.0, 'openclose2_total_fee_rebate': 0, 'openclose2_open_orders': 0, 'openclose2_cumulative_deposits': 18231000000, 'openclose2_m0_base_asset_amount': 2.885736343763763e+16, 'openclose2_m0_quote_asset_amount': 18231000000, 'openclose2_m0_last_cumulative_funding_rate': -74, 'openclose2_m0_last_funding_rate_ts': 0, 'openclose2_m0_upnl': -288293.816242218, 'openclose2_m0_upnl_noslip': -18230981719.433006, 'openclose2_m0_ufunding': 0.0, 'openclose2_total_collateral': 18048401706.183758, 'openclose3_collateral': 27204210000.0, 'openclose3_free_collateral': 24297284378.42394, 'openclose3_margin_ratio': 0.9795852773788252, 'openclose3_total_position_value': 27623568746.88733, 'openclose3_total_fee_paid': 274790000.0, 'openclose3_total_fee_rebate': 0, 'openclose3_open_orders': 0, 'openclose3_cumulative_deposits': 27479000000, 'openclose3_m0_base_asset_amount': -4.34265982565888e+16, 'openclose3_m0_quote_asset_amount': 27479000000, 'openclose3_m0_last_cumulative_funding_rate': 0, 'openclose3_m0_last_funding_rate_ts': 0, 'openclose3_m0_upnl': -144568746.8873291, 'openclose3_m0_upnl_noslip': 27479027509.888092, 'openclose3_m0_ufunding': -32.13568270987571, 'openclose3_total_collateral': 27059641253.11267, 'timestamp': 341} 
bad = {'m0_mark_price': 6.334801526388191, 'm0_oracle_price': 20.80728147496417, 'm0_bid_price': 6.33480152638819, 'm0_ask_price': 6.33480152638819, 'm0_wouldbe_peg': 6.355, 'm0_wouldbe_peg_cost': 0.0, 'm0_predicted_long_funding': -0.00022218977311345997, 'm0_predicted_short_funding': -0.00022218977311345997, 'm0_last_mid_price_twap': 6.318663332965472, 'm0_repeg_to_oracle_cost': -21019.110879882268, 'm0_market_index': 0, 'm0_base_asset_amount_long': 2.885736343763763e+16, 'm0_base_asset_amount_short': -4.34265982565888e+16, 'm0_base_asset_amount': -1.4569234818951168e+16, 'm0_total_base_asset_amount': 0, 'm0_open_interest': 2, 'm0_total_exchange_fees': 0.0, 'm0_total_mm_fees': 0.0, 'm0_margin_ratio_initial': 1000, 'm0_margin_ratio_maintenance': 625, 'm0_margin_ratio_partial': 500, 'm0_base_asset_reserve': '10015929779701538816', 'm0_quote_asset_reserve': '9984095555727812608', 'm0_funding_period': 60, 'm0_sqrt_k': 1e+19, 'm0_peg_multiplier': 6355, 'm0_total_lp_tokens': 1e+19, 'm0_lp_tokens': 1.0597008348382376e+19, 'm0_cumulative_lp_funding': -321356827098757.1, 'm0_last_funding_rate': -74, 'm0_last_funding_rate_ts': 274, 'm0_cumulative_funding_rate_long': -74, 'm0_cumulative_funding_rate_short': -74, 'm0_last_oracle_price': 18.67176461391388, 'm0_last_oracle_conf': 0, 'm0_last_oracle_normalised_price': 6.355578474019053, 'm0_last_oracle_price_twap': 13.537084903264308, 'm0_last_oracle_price_twap_ts': 314, 'm0_last_mark_price': 0, 'm0_last_mark_price_twap': 6.318360527406851, 'm0_last_bid_price_twap': 6.318663332965472, 'm0_last_ask_price_twap': 6.318663332965472, 'm0_last_mark_price_twap_ts': 314, 'm0_net_base_asset_amount': -1.4569234818951168e+16, 'm0_net_quote_asset_amount': -45710000000, 'm0_base_spread': 0, 'm0_mark_std': 0.0, 'm0_buy_intensity': 0, 'm0_sell_intensity': 0, 'm0_last_spread': 0, 'm0_bid_price_before': 6.300494999448206, 'm0_ask_price_before': 6.300494999448206, 'm0_total_fee': 457.1, 'm0_total_fee_minus_distributions': 445.4936527660969, 'm0_strategies': '', 'm0_minimum_quote_asset_trade_size': 10000000, 'm0_quote_asset_amount_long': 18231000000, 'm0_quote_asset_amount_short': 27479000000, 'm0_terminal_quote_asset_reserve': 1e+19, 'LP0_collateral': 78099056330.21126, 'LP0_free_collateral': 78093630896.69681, 'LP0_margin_ratio': 1459.4056565175122, 'LP0_total_position_value': 53514238.46533939, 'LP0_total_fee_paid': 0, 'LP0_total_fee_rebate': 0, 'LP0_open_orders': 0, 'LP0_cumulative_deposits': 78096592245, 'LP0_m0_base_asset_amount': 84477295142176.45, 'LP0_m0_quote_asset_amount': 53588248.13326977, 'LP0_m0_last_cumulative_funding_rate': -74, 'LP0_m0_last_funding_rate_ts': 332, 'LP0_m0_upnl': -74009.66793037951, 'LP0_m0_upnl_noslip': -53588194.618579954, 'LP0_m0_ufunding': 0.0, 'LP0_total_collateral': 78098982320.54333, 'LP1_collateral': 680710160811.0227, 'LP1_free_collateral': 680614549562.1349, 'LP1_margin_ratio': 732.4098373045991, 'LP1_total_position_value': 929407902.0804387, 'LP1_total_fee_paid': 0, 'LP1_total_fee_rebate': 0, 'LP1_open_orders': 0, 'LP1_cumulative_deposits': 680701018549, 'LP1_m0_base_asset_amount': -1466931167937250.0, 'LP1_m0_quote_asset_amount': 926737443.400641, 'LP1_m0_last_cumulative_funding_rate': -74, 'LP1_m0_last_funding_rate_ts': 341, 'LP1_m0_upnl': -2670458.6797977686, 'LP1_m0_upnl_noslip': 926738372.6724211, 'LP1_m0_ufunding': -0.0, 'LP1_total_collateral': 680707490352.3429, 'openclose2_collateral': 18048690000.0, 'openclose2_free_collateral': 16222934379.334282, 'openclose2_margin_ratio': 0.9899983812367531, 'openclose2_total_position_value': 18228049310.371426, 'openclose2_total_fee_paid': 182310000.0, 'openclose2_total_fee_rebate': 0, 'openclose2_open_orders': 0, 'openclose2_cumulative_deposits': 18231000000, 'openclose2_m0_base_asset_amount': 2.885736343763763e+16, 'openclose2_m0_quote_asset_amount': 18231000000, 'openclose2_m0_last_cumulative_funding_rate': -74, 'openclose2_m0_last_funding_rate_ts': 0, 'openclose2_m0_upnl': -2950689.6285743713, 'openclose2_m0_upnl_noslip': -18230981719.433006, 'openclose2_m0_ufunding': 0.0, 'openclose2_total_collateral': 18045739310.371426, 'openclose3_collateral': 27204210000.0, 'openclose3_free_collateral': 24290558063.68484, 'openclose3_margin_ratio': 0.9791471677444163, 'openclose3_total_position_value': 27629683578.468327, 'openclose3_total_fee_paid': 274790000.0, 'openclose3_total_fee_rebate': 0, 'openclose3_open_orders': 0, 'openclose3_cumulative_deposits': 27479000000, 'openclose3_m0_base_asset_amount': -4.34265982565888e+16, 'openclose3_m0_quote_asset_amount': 27479000000, 'openclose3_m0_last_cumulative_funding_rate': 0, 'openclose3_m0_last_funding_rate_ts': 0, 'openclose3_m0_upnl': -150683578.46832657, 'openclose3_m0_upnl_noslip': 27479027509.888092, 'openclose3_m0_ufunding': -32.13568270987571, 'openclose3_total_collateral': 27053526421.531673, 'timestamp': 341} 

for k in good: 
    if type(good[k]) == str: continue
    if k not in bad: 
        print(f'{k} missing')
        continue
    diff = abs(bad[k] - good[k])
    if diff > 0: 
        print(k, diff)

#%%
#%%
#%%
#%%
#%%
#%%
#%%
#%%