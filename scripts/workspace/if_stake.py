## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

# %%
# %reload_ext autoreload
# %autoreload 2

import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
# sys.path.insert(0, './driftpy/src/')
sys.path.insert(0, '../../driftpy/src/')
sys.path.insert(0, '../../')

import driftpy
import os 
import datetime
import math 
import numpy as np 

from tqdm.notebook import tqdm 
from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

import json 
import numpy as np 
import pandas as pd

from sim.helpers import *
from sim.agents import * 

from sim.driftsim.clearing_house.math.pnl import *
from sim.driftsim.clearing_house.math.amm import *
from sim.driftsim.clearing_house.state import *
from sim.driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 

import pathlib 
import pandas as pd 
import random 

def setup_ch():
    markets = []

    # # market one 
    # oracle_df = pd.read_csv('../../experiments/init/uponly/oracle.csv', index_col=[0])    
    # prices = oracle_df.values
    # timestamps = (oracle_df.index-oracle_df.index[0])
    prices = []
    start = 0.01; 
    x = start
    for _ in range(2000):
        x += min(0.2, 0.8 * x)
        prices.append(x)
    timestamps = np.arange(len(prices))

    oracle = Oracle(prices=prices, timestamps=timestamps)
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=367_621_0 * AMM_RESERVE_PRECISION,
        quote_asset_reserve=367_621_0 * AMM_RESERVE_PRECISION,
        funding_period=3600,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
    )
    market = SimulationMarket(amm=amm, market_index=0)
    markets.append(market)

    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse(markets, fee_structure)

    return ch

def main():
    ## EXPERIMENTS PATH 
    path = pathlib.Path('../../experiments/init/if_stake')
    path.mkdir(exist_ok=True, parents=True)
    print(str(path.absolute()))

    seed = np.random.randint(0, 1e3)
    np.random.seed(seed)
    random.seed(seed)
    print('seed', seed)

    # setup markets + clearing houses
    ch = setup_ch()

    # setup the agents
    n_lps = 0
    n_traders = 10
    n_times = 1
    n_stakers = 10
    total_users = n_lps + n_traders + n_stakers

    n_markets = len(ch.markets)
    max_t = [len(market.amm.oracle) for market in ch.markets]
    print(max_t)

    agents = []

    # if stakers add  (and never remove)
    for i in range(n_stakers):
        agents.append(
            IFStaker(
                100 * QUOTE_PRECISION, 
                0, 
                i, 
                start_time=0, 
                duration=400 if np.random.randint(0, 2) else max_t[0], 
            )
        )

    # people open positions (and never close) 
    for i in range(n_stakers, n_stakers+n_traders):
        agents.append(
            OpenClose(
                start_time=0+ 5*(i - n_stakers), 
                duration=max_t[0], 
                direction='short',
                user_index=i, 
                market_index=0
            )
        )

    # settle pnl so oracle updates
    for i in range(total_users):
        update_every = np.random.randint(100, max_t[0] // 4)
        agents.append(
            SettlePnL.random_init(max_t[0], i, 0, update_every)
        )
    
    # people should get liqd ... 

    # more stakers add
    t = 600

    for i in range(total_users, total_users+n_stakers):
        agents.append(
            IFStaker(
                100 * QUOTE_PRECISION, 
                0, 
                i, 
                start_time=t + 5*(i - total_users), 
                duration=max_t[0], 
            )
        )

    # settle pnl so oracle updates
    for i in range(total_users, total_users+n_stakers):
        update_every = np.random.randint(200, max_t[0] // 4)
        agents.append(
            SettlePnL.random_init(max_t[0], i, 0, start=t, update_every=update_every)
        )

    # !! 
    from helpers import run_trial
    run_trial(agents, ch, path)

if __name__ == '__main__':
    main()