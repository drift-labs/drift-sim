## this notebook ensures the collateral of all users / lps add up if everyone 
## were to close 

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
from sim.driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 
from sim.driftsim.clearing_house.state import *

import pathlib 
import pandas as pd 
import random 

def setup_ch(base_spread=0, strategies='', n_steps=100):

    # market one 
    down_probs = 0.0
    prices, timestamps = random_walk_oracle(90, n_steps=n_steps, down_up_probs=[down_probs, 1-down_probs], std=0.02)
    oracle = Oracle(prices=prices, timestamps=timestamps)

    # oracle_df = pd.read_csv('../../experiments/init/uponly/oracle.csv', index_col=[0])    
    # prices = oracle_df.values
    # timestamps = (oracle_df.index-oracle_df.index[0])
    # oracle = Oracle(prices=prices, timestamps=timestamps)

    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        quote_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        funding_period=3600,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
        base_spread=base_spread,
        strategies=strategies,
    )
    market = SimulationMarket(amm=amm, market_index=0)
    markets = [market]

    spot_markets = []
    # prices, time = rand_heterosk_oracle(1, n_steps=n_steps)
    prices = [1] * n_steps
    time = np.array(list(range(len(prices))))
    spot_markets.append(
        SimulationSpotMarket(
            oracle=Oracle(prices=prices, timestamps=time)
        )
    )
    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse(markets, fee_structure, spot_markets=spot_markets)

    return ch

def main():
    ## EXPERIMENTS PATH 
    path = pathlib.Path(f'../../experiments/init/{pathlib.Path(__file__).stem}')
    path.mkdir(exist_ok=True, parents=True)
    print(str(path.absolute()))

    seed = np.random.randint(0, 1e3)
    np.random.seed(seed)
    random.seed(seed)
    print('seed', seed)

    # setup markets + clearing houses
    n_steps = 500
    ch = setup_ch(
        n_steps=n_steps,
        base_spread=0,
    )
    n_markets = len(ch.markets)
    n_spot_markets = len(ch.spot_markets) + 1
    max_t = [len(market.amm.oracle) for market in ch.markets]
    max_max_t = max(max_t)

    # test agents seperate rn then do multiple agents on a sinlge user later
    n_lps = 5
    n_traders = 5
    n_stakers = 5
    n_borrows = 5
    n_times = 3
    total_users = n_lps + n_traders + n_stakers + n_borrows

    agents = []

    # liquidator deposits in 0 and borrows from 1 
    agent = Liquidator(0, deposits=[100_000 * QUOTE_PRECISION, 0], every_t_times=1)
    agents.append(agent)
    agent = Borrower(
        0,
        1,
        0,
        70_000 * QUOTE_PRECISION,
        user_index=0,
        start_time=0,
        duration=max_max_t,
    )
    agents.append(agent)

    # agent deposits in 1 and borrows from 0 
    # 30K left in spot 0
    agent = Borrower(
        1, 
        0, 
        100_000 * QUOTE_PRECISION, 
        70_000 * QUOTE_PRECISION, 
        user_index=1,
        start_time=0,  
        duration=max_max_t,
    )
    agents.append(agent)
    
    # agent2 deposits in 1 and borrows from 0 -- spot0 utilization at 99.99%
    agent = Borrower(
        1, 
        0, 
        100_000 * QUOTE_PRECISION, 
        # 30_000 * QUOTE_PRECISION, # interest
        29_999 * QUOTE_PRECISION, # interest
        user_index=2,
        start_time=0,  
        duration=max_max_t,
    )
    agents.append(agent)

    # trader - opens short - price goes up and he gets settled 
    for i in range(n_traders):
        agent = SettlePnL(3+i, 0, 50)
        agents.append(agent)

        agent = OpenClose.random_init(100, 3+i, 0, spot_market_index=1, short_bias=1.)
        agent.start_time = min(100, n_steps//2)
        agent.duration = n_steps # dont close until end
        agents.append(agent)

    # # traders -- trade with spot 1 (note pnl is settled in spot0)
    # for i in range(n_traders):
    #     user_idx = 3+i
    #     agent = MultipleAgent(
    #         lambda: OpenClose.random_init(max_t[0], user_idx, 0, 1, short_bias=0.9),
    #         n_times, 
    #     )
    #     agents.append(agent)

    for i in range(n_traders, n_traders + n_lps):
        agent = MultipleAgent(
            lambda: AddRemoveLiquidity.random_init(max_t[0], 3 + i, 0, min_token_amount=100000, spot_market=1),
            n_times, 
        )

    #     update_every = np.random.randint(1, max_t[0] // 4)
    #     agents.append(
    #         SettlePnL.random_init(max_t[0], 3+i, 0, update_every)
    #     )

    for i in range(n_stakers):
        agents.append(
            IFStaker.random_init(max(max_t), i, 0)
        )

    # !! 
    from helpers import run_trial
    run_trial(agents, ch, path)

if __name__ == '__main__':
    main()