import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, '../../driftpy/src/')
sys.path.insert(0, '../../')

from sim.agents import * 
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
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field
import random
from pathlib import Path

from sim.helpers import *
from sim.driftsim.clearing_house.math.pnl import *
from sim.driftsim.clearing_house.math.amm import *
from sim.driftsim.clearing_house.state import *
from sim.driftsim.clearing_house.lib import *

from sim.events import * 
from sim.agents import * 

def setup_ch(base_spread=0, strategies='', n_steps=100):
    oracle_df = pd.read_csv('../../experiments/init/lunaCrash/oracle.csv', index_col=[0])
    prices = oracle_df.values
    timestamps = (oracle_df.index-oracle_df.index[0])
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
    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse([market], fee_structure)

    return ch

def main():
    seed = np.random.randint(0, 1e3)
    np.random.seed(seed)
    random.seed(seed)
    print('seed', seed)

    ch = setup_ch(
        n_steps=100,
        base_spread=0,
    )
    market: SimulationMarket = ch.markets[0]

    n_lps = 5
    n_traders = 5

    # init agents
    agents = []
    max_t = len(market.amm.oracle)

    agents += [ 
        MultipleAgent(
            lambda: OpenClose.random_init(max_t, user_idx, 0, short_bias=0.9),
            20, 
        )
        for user_idx in range(n_traders)
    ]

    n = len(agents)
    agents += [ 
        MultipleAgent(
            lambda: AddRemoveLiquidity.random_init(max_t, user_idx, 0, min_token_amount=100000),
            20, 
        )
        for user_idx in range(n, n + n_lps)
    ]

    from helpers import run_trial
    path = Path('../../experiments/init/lunaCrash')
    run_trial(agents, ch, path)

if __name__ == '__main__':
    main()