# %%
# !pip install plotly
# !pip install matplotlib

# %%
# %reload_ext autoreload
# %autoreload 2

import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, './driftpy/src/')
sys.path.insert(0, '../driftpy/src/')
sys.path.insert(0, '../')

import driftpy

import os 
import datetime

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction
)
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl, calculate_position_funding_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price
from driftpy.math.user import *

from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PEG_PRECISION

from solana.publickey import PublicKey

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

#%%
SIM_NAME = 'sim-results/sim-crosscheck'
os.makedirs(SIM_NAME, exist_ok=True)

maintenant = datetime.datetime.utcnow()
maintenant_str = maintenant.strftime("%Y/%m/%d %H:%M:%S UTC")
with open(os.path.join(SIM_NAME,'run_info.json'), 'w') as f:
    json.dump({'run_time': maintenant_str}, f)

prices, timestamps = rand_heterosk_oracle(1)
oracle = Oracle(prices=prices, timestamps=timestamps)

max_t = max(timestamps)
all_timestamps = list(range(max_t))
all_prices = [int(oracle.get_price(t) * 1e10) for t in all_timestamps]

# save to file -- easier to cross reference with per-timestamp prices  
oracle_df = pd.DataFrame({'timestamp': all_timestamps, 'price': all_prices})
oracle_df.to_csv(SIM_NAME+"/all_oracle_prices.csv", index=False)

pd.DataFrame(oracle.prices).plot()

# %%
def setup_ch(oracle: Oracle):
    start_price = oracle.get_price(0)
    amm = AMM(
        oracle=oracle, 
        base_asset_reserve=1e13, 
        quote_asset_reserve=1e13,
        funding_period=60,
        peg_multiplier=int(start_price*1e3),
        base_spread=0,
    )
    market = Market(amm)
    fee_structure = FeeStructure(numerator=1, denominator=100)
    clearing_house = ClearingHouse([market], fee_structure)
    return clearing_house    

def run_sim(oracle: Oracle):
    clearing_house = setup_ch(oracle)
        
    simulation_results = {
        'events': [], 
        'clearing_houses': [],
    }
    oracle_length = len(oracle)
    print('running simulation for %i timesteps' % oracle_length)
    
    # timestamp 0 
    noop = NullEvent(timestamp=clearing_house.time)
    simulation_results['events'].append(noop)
    simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
    clearing_house.change_time(+1)

    # define + setup agents 
    arb_agent1 = Arb(
        intensity=1, 
        market_index=0, 
        user_index=0
    )
    agents = [arb_agent1]    
    
    # timestamp 1 -- setup agent
    init_user = DepositCollateralEvent(
        user_index=0, 
        deposit_amount=1_000 * QUOTE_PRECISION, 
        timestamp=clearing_house.time,
    )
    clearing_house = init_user.run(clearing_house)
    simulation_results['events'].append(init_user)
    simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
    clearing_house.change_time(1)
    
    # run simulation
    for _ in range(oracle_length):
        
        for i, agent in enumerate(agents):
            event_i: Event = agent.run(clearing_house)
            clearing_house = event_i.run(clearing_house)
            
            simulation_results['events'].append(event_i)
            simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
    
        clearing_house = clearing_house.change_time(+1)
    
    return simulation_results

simulation_results = run_sim(oracle)

# %%
result_dfs = [pd.DataFrame(ch.to_json(), index=[i]) for i, ch in enumerate(simulation_results['clearing_houses'])]
result_df = pd.concat(result_dfs)
result_df.to_csv(SIM_NAME+"/simulation_state.csv", index=False)
result_df.head()

# %%
event_rows = [e.serialize_to_row() for e in simulation_results['events']]
simulation_df = pd.DataFrame.from_dict(event_rows)
simulation_df.to_csv(SIM_NAME+"/events.csv", index=False)
simulation_df.head()

# %%
SIM_NAME

# %%


