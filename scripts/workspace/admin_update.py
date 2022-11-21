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
        funding_period=1,
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
    n_steps = 300
    ch: ClearingHouse = setup_ch(
        n_steps=n_steps,
        base_spread=0,
    )
    n_markets = len(ch.markets)
    n_spot_markets = len(ch.spot_markets) + 1
    max_t = [len(market.amm.oracle) for market in ch.markets]
    max_max_t = max(max_t)

    # test agents seperate rn then do multiple agents on a sinlge user later
    n_lps = 5
    n_traders = 10
    n_stakers = 5
    n_borrows = 5
    n_times = 3
    total_users = n_lps + n_traders + n_stakers + n_borrows

    agents = []

    # liquidator deposits in 0 and borrows from 1 
    agent = Liquidator(0, deposits=[100_000 * QUOTE_PRECISION, 0], every_t_times=1)
    agents.append(agent)

    # sqrt k updates
    n_k_updates = 10
    k_updates = []
    last_sqrt_k = int(ch.markets[0].amm.sqrt_k)
    for i in range(n_k_updates):
        sqrt_up = 1 if np.random.randint(0, 1) else 0
        if sqrt_up:
            new_sqrt_1 = int(last_sqrt_k * 1.0000002)
            k = UpdateKEvent(100 + i * 50, new_sqrt_1, 0)
        else:
            new_sqrt_1 = int(last_sqrt_k * 0.99998)
            k = UpdateKEvent(100 + i * 50, new_sqrt_1, 0)

        assert new_sqrt_1 != last_sqrt_k
        last_sqrt_k = new_sqrt_1
        k_updates.append(k)

    repegs = [
        RepegEvent(
            100, 
            -1,
            0
        )
    ]
    agent = Admin(
        k_updates, 
        repegs,
    )
    agents.append(agent)

    for i in range(n_traders):
        # agent = SettlePnL(1+i, 0, 50)
        # agents.append(agent)

        agent = OpenClose.random_init(100, 1+i, 0, spot_market_index=1, short_bias=1.)
        agent.start_time = min(100, n_steps//2)
        agent.duration = 10 if i % 2 else n_steps # dont close until end
        agents.append(agent)

    # !! 
    from helpers import run_trial
    run_trial(agents, ch, path)


if __name__ == '__main__':
    main()