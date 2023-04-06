import pandas as pd
pd.options.plotting.backend = "plotly"


import sys
sys.path.insert(0, '../../driftpy/src/')
sys.path.insert(0, '../../')
sys.path.insert(0, '/home/mstelluti/Projects/drift-sim/')
sys.path.insert(0, '/home/mstelluti/Projects/drift-sim/driftpy/src/')

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
import numpy as np 
import pandas as pd
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



def setup_ch(start_price, n_steps, quote_asset_reserve):
    """
    Sets up the clearing house with one market and a simulation AMM.

    Args:
        start_price (float): The starting price of the oracle.
        n_steps (int): The number of steps to generate for the oracle.
        quote_asset_reserve (int): The amount of quote assets in the AMM reserve. 

    Returns:
        ClearingHouse: The initialized clearing house.
    """
    
    # First n_step prices 
    # prices, _ = rand_heterosk_oracle(start_price, n_steps=n_steps)
    
    # Add 4x market move prices 
    price_multiple=np.array([1, 1.1, 1.2, 1.3, 1.4, 2.1, 1.5, 3.5, 4, 4.05, 3.95, 4])
    # extra_prices = prices[0] * price_multiple
    extra_prices = start_price * price_multiple
    # prices = np.append(prices, extra_prices)
    prices = extra_prices

    # Add 20 more prices after 4x move
    # prices_to_add, _ = rand_heterosk_oracle(prices[-1], n_steps=n_steps)
    # prices = np.append(prices, prices_to_add)

    # Timestamps
    timestamps = np.arange(len(prices))

    # Set up Oracle
    oracle = Oracle(prices=prices, timestamps=timestamps)

    # Set up the AMM
    # base_asset_reserve = quote_asset_reserve * AMM_RESERVE_PRECISION  # e.g. BTC
    # quote_asset_reserve = quote_asset_reserve * AMM_RESERVE_PRECISION  # amount in USD AMM is willing to buy of base asset BTC

    # Large OI
    amm = SimulationAMM(
        oracle=oracle,
        base_asset_reserve=quote_asset_reserve,
        quote_asset_reserve=quote_asset_reserve,
        funding_period=3600,
        peg_multiplier=int(oracle.get_price(0)*PEG_PRECISION),
    )

    # Set up the market
    market = SimulationMarket(amm=amm, market_index=0)

    # Set up the clearing house with one market
    markets = [market]

    # Setup spot market 
    spot_markets = []
    # prices, time = rand_heterosk_oracle(1, n_steps=n_steps)
    prices_spot = [1] * len(prices)

    spot_markets.append(
        SimulationSpotMarket(
            oracle=Oracle(prices=prices_spot, timestamps=timestamps)
        )
    )
    
    fee_structure = FeeStructure(numerator=1, denominator=1000)
    ch = ClearingHouse(markets, fee_structure, spot_markets=spot_markets)

    return ch


def main():

    path = Path('/home/mstelluti/Projects/drift-sim/experiments/init/sim_4x')
    path.mkdir(exist_ok=True, parents=True)

    # Size of AMM quote asset reserve 
    QUOTE_ASSET_RESERVE = 1_000_000 * AMM_RESERVE_PRECISION
    # Num steps of prices
    NUM_STEPS = 20
    # Leverage
    LEVERAGE = 10
    # 10 Long, 10 Short
    NUM_TRADERS = 10
 
    # Store clearing house objects
    clearing_houses = [] # clearing_houses.append(copy.deepcopy(ch))
    
    # Store Event objects
    events = []

    # Store Agent objects
    agents = []

    # Create Clearing House
    ch = setup_ch(start_price=90, n_steps=NUM_STEPS, quote_asset_reserve=QUOTE_ASSET_RESERVE)
    original_ch = copy.deepcopy(ch)  # store original for final run_event_trial() simulation
    clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list

    # Create trade position sizes 
    amm_ask_quote = ch.markets[0].amm.ask_quote_asset_reserve
    # so total short OI 1.5x > AMM ask liquidity 
    short_trade_amount = 1.25 * amm_ask_quote / AMM_TO_QUOTE_PRECISION_RATIO / NUM_TRADERS  # 0.2 of the AMM quote_asset_reserve 
    long_trade_amount = amm_ask_quote / AMM_TO_QUOTE_PRECISION_RATIO / NUM_TRADERS

    for trader in range(NUM_TRADERS): 

        print(f"ClearingHouse time: {ch.time} \n")

        ###############
        # Short traders
        ###############

        # Deposit short traders' collateral 
        event = DepositCollateralEvent(
            user_index=trader, 
            # 0.1 trade size, to reflect 10x leverage -- subtract 0.25 from the divisor to prevent margin requirement failure, so leverage is actually 9.75
            deposit_amount=short_trade_amount / (LEVERAGE-0.25), 
            timestamp=ch.time,
        )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list

        # Open short positions 
        event = OpenPositionEvent(
                    user_index=trader, # user_index 0 -> 9
                    direction='short',
                    quote_amount=short_trade_amount,
                    market_index=0,
                    timestamp=ch.time
                )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list
        
        ###############
        # Long traders
        ###############

        # Deposit long traders' collateral 
        event = DepositCollateralEvent(
            user_index=trader+NUM_TRADERS, # user_index 10 -> 19 
            deposit_amount=long_trade_amount,
            timestamp=ch.time,
        )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list

        # Open long positions
        event = OpenPositionEvent(
                    user_index=trader+NUM_TRADERS, # user_index 10 -> 19    
                    direction='long',
                    quote_amount=long_trade_amount,
                    market_index=0,
                    timestamp=ch.time
                )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list

        # Spread out events to setup 4x simulation over 5 time steps before the 4x move 
        if trader % 2 == 0:
            ch.change_time(1)

    # Change time to timestep of the 4x price
    # ch.change_time(NUM_STEPS+8-ch.time) 
    ch.change_time(8-ch.time) 
    print(f"ClearingHouse time {ch.time} \n")
        
    # Liquidator deposits in spot market 0, starts liquidating   
    agent = Liquidator(user_index=0, deposits=[100_000 * QUOTE_PRECISION], every_t_times=1)
    agents.append(agent)

    # Longs Close and Withdraw, Shorts Close 
    for trader in range(NUM_TRADERS):
        print(f"ClearingHouse time {ch.time} \n")

        # Shorts close 
        # event = ClosePositionEvent(
        #         market_index=0,
        #         user_index=trader,
        #         timestamp=ch.time,
        #     )
        # ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        # events.append(event)  # append Event object to list

        # # Get position size being closed
        # user_after: User = ch.users[trader]
        # position_after = user_after.positions[0]
        # market: SimulationMarket = ch.markets[0]
            
        # unrealized_pnl = driftpy.math.positions.calculate_position_pnl( market, position_after )

        # entry_price = calculate_entry_price(position_after)

        # Longs Close 
        event = ClosePositionEvent(
                market_index=0,
                user_index=trader+NUM_TRADERS,
                timestamp=ch.time,
            )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list

        # Get position size being closed
        # user_after: User = ch.users[trader+NUM_TRADERS]
        # position_after = user_after.positions[0]
        # market_after: SimulationMarket = ch.markets[0]
        # entry_price = calculate_entry_price(position_after)    
        # unrealized_pnl = driftpy.math.positions.calculate_position_pnl( market_after, position_after )
        
        # New Long collateral post-close
        user: User = ch.users[trader+NUM_TRADERS]
        collateral = user.collateral

        # Longs Withdraw full amount
        event = WithdrawEvent(
            user_index=trader+NUM_TRADERS,
            spot_market_index=0,
            withdraw_amount=collateral,
            reduce_only=True,
            timestamp=ch.time,
            )
        ch = event.run(ch, verbose=True)  # Run Event in the ClearingHouse and create updated ch
        events.append(event)  # append Event object to list
        clearing_houses.append(copy.deepcopy(ch))  # append ClearingHouse object to list


    # Pre-agent events and clearing house objects 
    # json_events = [e.serialize_to_row() for e in events if e._event_name != 'null']
    # df = pd.DataFrame(json_events)
    # df.to_csv(path/'events_noagent.csv', index=False)
    # json_chs = [e.to_json() for e in clearing_houses]
    # df = pd.DataFrame(json_chs)
    # df.to_csv(path/'chs_noagent.csv', index=False)

    # Run the trial to generate Events from Agents
    from helpers import run_trial
    events_from_agents, _, chs_from_agents = run_trial(agents, ch, path)
    
    # Append events and clearing houses generated from run_trial()
    events+=events_from_agents
    clearing_houses+=chs_from_agents

    # Run trial with all events
    from helpers import run_trial_events
    run_trial_events(events, original_ch, path)

if __name__ == '__main__':
    main()