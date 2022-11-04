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

def setup_ch(base_spread=0, strategies='', n_steps=100):
    prices, timestamps = random_walk_oracle(1, n_steps=n_steps)
    oracle = Oracle(prices=prices, timestamps=timestamps)
    
    amm = SimulationAMM(
        oracle=oracle, 
        base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
        quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
        funding_period=60,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
        base_spread=base_spread,
        strategies=strategies
    )
    market = SimulationMarket(amm=amm, market_index=0)   
    fee_structure = FeeStructure(numerator=1, denominator=100)
    ch = ClearingHouse([market], fee_structure)

    return ch

def main():
    seed = 85
    np.random.seed(seed)
    print('seed', seed)

    ch = setup_ch(
        n_steps=100,
        base_spread=0,
    )

    events = [
        DepositCollateralEvent(timestamp=0, user_index=0, deposit_amount=1998590197697, username='LP', _event_name='deposit_collateral'),
        DepositCollateralEvent(timestamp=1, user_index=1, deposit_amount=4255468411490, username='LP', _event_name='deposit_collateral'),
        DepositCollateralEvent(timestamp=4, user_index=2, deposit_amount=79010000000, username='openclose', _event_name='deposit_collateral'),
        DepositCollateralEvent(timestamp=5, user_index=3, deposit_amount=1802000000, username='openclose', _event_name='deposit_collateral'),

        addLiquidityEvent(timestamp=142, market_index=0, user_index=1, token_amount=42554684114, _event_name='add_liquidity'),
        SettleLPEvent(timestamp=183, user_index=1, market_index=0, _event_name='settle_lp'),
        OpenPositionEvent(timestamp=227, user_index=2, direction='long', quote_amount=790100000, market_index=0, _event_name='open_position'),

        removeLiquidityEvent(timestamp=10000000000227.0, market_index=0, user_index=1, lp_token_amount=-1, _event_name='remove_liquidity'),
        ClosePositionEvent(timestamp=10000000000228.0, user_index=1, market_index=0, _event_name='close_position'),
        ClosePositionEvent(timestamp=10000000000229.0, user_index=2, market_index=0, _event_name='close_position'),
    ]

    from helpers import run_trial_events
    path = Path('../../experiments/init/add_open_remove_close')
    run_trial_events(events, ch, path)

if __name__ == '__main__':
    main()