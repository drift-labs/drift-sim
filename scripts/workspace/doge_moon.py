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

from sim.driftsim.clearing_house.state import *

def setup_ch(base_spread=0, strategies=''):
    oracle_df = pd.read_csv('../../experiments/init/dogeMoon/oracle.csv', index_col=[0])    
    prices = oracle_df.values
    timestamps = (oracle_df.index-oracle_df.index[0])
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        quote_asset_reserve=367_621 * AMM_RESERVE_PRECISION,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
        base_spread=base_spread,
        strategies=strategies,
        # base_asset_amount_step_size=0,
        # minimum_quote_asset_trade_size=0,
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
        n_steps=1000,
        base_spread=0,
        strategies='PrePeg_OracleRetreat_InventorySkew'
    )

    # init agents
    arb_agent = Arb(
                    intensity=1, 
                    market_index=0,
                    user_index=0, 
                    lookahead=40,
                )
    agents = [arb_agent]
    print('#agents:', len(agents))

    from helpers import run_trial
    path = Path('../../experiments/init/dogeMoon')
    run_trial(agents, ch, path)

if __name__ == '__main__':
    main()