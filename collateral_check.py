## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

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

from sim.helpers import close_all_users, random_walk_oracle, rand_heterosk_oracle, class_to_json
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

n_lps = 2
n_trades = 2

# n_lps = 2
# n_trades = 2

class RandomSimulation():
    def __init__(self, ch: ClearingHouse) -> None:
        self.ch = ch 
        market: Market = ch.markets[0]
        self.max_t = len(market.amm.oracle)

        peg = market.amm.peg_multiplier / PEG_PRECISION
        sqrt_k = market.amm.sqrt_k / 1e13
        self.full_amm_position_quote = sqrt_k * peg * 2 * 1e6

    def generate_lp_settler(self, user_index, market_index) -> Agent:
        return SettleLP(
            user_index, 
            market_index, 
            every_x_steps=1, # tmp
        )

    def generate_lp(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, max_t)
        dur = np.random.randint(0, max_t // 2)
        amount = np.random.randint(0, full_amm_position_quote // (n_lps + 10))
        return LP(
            lp_start_time=start,
            lp_duration=dur, 
            deposit_amount=amount, 
            user_index=user_index, 
            market_index=market_index
        )

    def generate_trade(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, max_t)
        dur = np.random.randint(0, max_t // 2)
        amount = np.random.randint(0, 100_000)
        
        return OpenClose(
            start_time=start,
            duration=dur, 
            direction='long' if np.random.choice([0, 1]) == 0 else 'short',
            quote_amount=amount * QUOTE_PRECISION, 
            user_index=user_index, 
            market_index=market_index
        )

sim = RandomSimulation(ch)
agents = []
agents += [
    sim.generate_lp(i, 0) for i in range(n_lps)
]
# agents += [
#     sim.generate_lp_settler(i, 0) for i in range(n_lps)
# ]
agents += [
    sim.generate_trade(i, 0) for i in range(n_lps, n_lps+n_trades)
]

def collateral_difference(ch, initial_collatearl, verbose=False):
    clearing_house = copy.deepcopy(ch)

    clearing_house, (chs, events, mark_prices) = close_all_users(clearing_house, verbose)
    
    # ensure collateral still adds up 
    current_total_collateral = 0
    for (_, user) in clearing_house.users.items():
        current_total_collateral += user.collateral
    end_total_collateral = current_total_collateral + market.amm.total_fee_minus_distributions
    end_total_collateral /= 1e6
    abs_difference = abs(initial_collatearl - end_total_collateral) 
    
    return abs_difference, events, chs, mark_prices

print('#agents:', len(agents))

mark_prices = []
events = []
clearing_houses = []
differences = []

# setup agents
for agent in agents:        
    event = agent.setup(ch)
    ch = event.run(ch)
    
    events.append(event)
    clearing_houses.append(copy.deepcopy(ch))
    differences.append(0)
    
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
# record total collateral pre trades     
def compute_total_collateral(ch):
    total_collateral = 0 
    init_collaterals = {}
    for (i, user) in ch.users.items():
        init_collaterals[i] = user.collateral
        total_collateral += user.collateral 
    
    for market_index in range(len(ch.markets)):
        market: Market = ch.markets[market_index]
        total_collateral += market.amm.total_fee_minus_distributions

    total_collateral /= 1e6
    return total_collateral

ch = setup_ch(
    base_spread=0, 
    strategies='',
    n_steps=100,
    n_users=0,
)

init_events = [
    DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=78096592245, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=1, user_index=1, deposit_amount=680701018549, username='LP', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=2, user_index=2, deposit_amount=18231000000, username='openclose', _event_name='deposit_collateral'),
    DepositCollateralEvent(timestamp=3, user_index=3, deposit_amount=27479000000, username='openclose', _event_name='deposit_collateral'),
]
for e in init_events: ch = e.run(ch)

total_collateral = compute_total_collateral(ch)

events = [
    addLiquidityEvent(timestamp=227, market_index=0, user_index=0, quote_amount=78096592245, _event_name='add_liquidity'),
    OpenPositionEvent(timestamp=274, user_index=3, direction='short', quote_amount=27479000000, market_index=0, _event_name='open_position'),
    addLiquidityEvent(timestamp=290, market_index=0, user_index=1, quote_amount=680701018549, _event_name='add_liquidity'),
    OpenPositionEvent(timestamp=314, user_index=2, direction='long', quote_amount=18231000000, market_index=0, _event_name='open_position'), 
]

_events = []
for e in events: 
    ch = e.run(ch)
    _events.append(e)

    abs_difference, close_events, _, _ = collateral_difference(ch, total_collateral, verbose=True)
    if abs_difference > 1:
        events += close_events
        print('blahhH!!!')
        break 
    
print(_events, close_events)
print(abs_difference)

#%%
#%%
#%%
#%%
#%%
#%%
#%%
