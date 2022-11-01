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
    prices, timestamps = rand_heterosk_oracle(90, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
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
    spot_markets.append(
        SimulationSpotMarket(
            oracle=Oracle(prices=[1] * len(prices), timestamps=timestamps), 
        )
    )

    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse(markets, fee_structure, spot_markets=spot_markets)

    return ch

def main():
    ## EXPERIMENTS PATH 
    path = pathlib.Path('../../experiments/init/spot2')
    path.mkdir(exist_ok=True, parents=True)
    print(str(path.absolute()))

    seed = np.random.randint(0, 1e3)
    np.random.seed(seed)
    random.seed(seed)
    print('seed', seed)

    # setup markets + clearing houses
    ch = setup_ch(
        n_steps=20,
        base_spread=0,
    )

    # setup the agents
    n_lps = 0
    n_traders = 1
    n_times = 1
    total_users = n_lps + n_traders

    n_markets = len(ch.markets)
    max_t = [len(market.amm.oracle) for market in ch.markets]

    events = [ 
        # user 0 deposits sudc 
        DepositCollateralEvent(0, 0, 100 * QUOTE_PRECISION, 0, 0, 'a'),
        # user 1 deposits sol
        DepositCollateralEvent(0, 1, 100 * 1e9, 1, 0, 'a'),
        # user 0 borrows sol 
        WithdrawEvent(0, 0, 1, 100_00, False)
    ]

    # !! 
    from helpers import run_trial_events
    run_trial_events(events, ch, path)

if __name__ == '__main__':
    main()