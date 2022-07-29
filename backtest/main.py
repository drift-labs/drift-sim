#%%
%reload_ext autoreload
%autoreload 2

import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../driftpy/src/')

import pandas as pd 
import numpy as np 

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

from driftpy.setup.helpers import _usdc_mint, _user_usdc_account, mock_oracle, _setup_user, set_price_feed, adjust_oracle_pretrade
from driftpy.clearing_house import ClearingHouse
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.accounts import get_market_account
from driftpy.math.amm import calculate_mark_price_amm
from driftpy.accounts import get_user_account

from anchorpy import Provider, Program, create_workspace
from programs.clearing_house.state.market import SimulationAMM, SimulationMarket
from helpers import setup_bank, setup_market, setup_new_user, view_logs

#%%
events = pd.read_csv("./sim-results/tmp/events.csv")
clearing_houses = pd.read_csv("./sim-results/tmp/chs.csv")
events

#%%
# setup clearing house + bank + market 
# note first run `anchor localnet` in v2 dir

path = '../driftpy/protocol-v2'
path = '/Users/brennan/Documents/drift/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
oracle_program: Program = workspace["pyth"]
provider: Provider = program.provider

clearing_house, usdc_mint = await setup_bank(
    program
)

init_state = clearing_houses.iloc[0]
init_reserves = int(init_state.m0_base_asset_reserve) # 200 * 1e13
init_market = SimulationMarket(
    market_index=0,
    amm=SimulationAMM(
        oracle=None,
        base_asset_reserve=init_reserves, 
        quote_asset_reserve=init_reserves, 
        funding_period = 60 * 60, # 1 hour dont worry about funding updates for now 
        peg_multiplier=int(init_state.m0_peg_multiplier),
    )
)
oracle = await setup_market(
    clearing_house, 
    init_market, 
    workspace
)

#%%
user_chs = {}
user_token_amount = {}
user_baa_amount = {}

init_total_collateral = 0 

for i in range(len(events)):
    event = events.iloc[i]
    
    if event.event_name == DepositCollateralEvent._event_name:
        event = Event.deserialize_from_row(DepositCollateralEvent, event)
        assert event.user_index not in user_chs, 'trying to re-init'
        print(f'=> {event.user_index} init user...')

        user_clearing_house, _ = await setup_new_user(
            provider, 
            program, 
            usdc_mint, 
            deposit_amount=event.deposit_amount
        )
        
        user_chs[event.user_index] = user_clearing_house
        init_total_collateral += event.deposit_amount

    elif event.event_name == OpenPositionEvent._event_name: 
        event = Event.deserialize_from_row(OpenPositionEvent, event)
        print(f'=> {event.user_index} opening position...')
        assert event.user_index in user_chs, 'user doesnt exist'

        # tmp -- sim is quote open position v2 is base only
        market = await get_market_account(program, 0)
        mark_price = calculate_price(
            market.amm.base_asset_reserve,
            market.amm.quote_asset_reserve,
            market.amm.peg_multiplier,
        )
        baa = int(event.quote_amount * AMM_RESERVE_PRECISION / QUOTE_PRECISION / mark_price)

        assert event.user_index not in user_baa_amount
        user_baa_amount[event.user_index] = baa

        ch: SDKClearingHouse = user_chs[event.user_index]
        direction = PositionDirection.LONG() if event.direction == 'long' else PositionDirection.SHORT()
        await adjust_oracle_pretrade(
            baa, 
            direction, 
            market, 
            oracle, 
            oracle_program
        )
        await ch.open_position(
            direction,
            baa, 
            event.market_index
        )

    elif event.event_name == ClosePositionEvent._event_name: 
        event = Event.deserialize_from_row(ClosePositionEvent, event)
        print(f'=> {event.user_index} closing position...')
        assert event.user_index in user_chs, 'user doesnt exist'

        ch: SDKClearingHouse = user_chs[event.user_index]
        baa = user_baa_amount[event.user_index] 
        direction = PositionDirection.LONG() if baa < 0 else PositionDirection.SHORT()
        market = await get_market_account(
            program, 
            0
        )
        await adjust_oracle_pretrade(
            baa, 
            direction, 
            market, 
            oracle, 
            oracle_program
        )
        await ch.close_position(event.market_index)

    elif event.event_name == addLiquidityEvent._event_name: 
        event = Event.deserialize_from_row(addLiquidityEvent, event)
        print(f'=> {event.user_index} adding liquidity...')
        assert event.user_index in user_chs, 'user doesnt exist'

        ch: SDKClearingHouse = user_chs[event.user_index]
        user_token_amount[event.user_index] = event.token_amount
        await ch.add_liquidity(
            event.token_amount, 
            event.market_index
        )

    elif event.event_name == removeLiquidityEvent._event_name:
        event = Event.deserialize_from_row(removeLiquidityEvent, event)
        print(f'=> {event.user_index} removing liquidity...')
        assert event.user_index in user_chs, 'user doesnt exist'

        burn_amount = event.lp_token_amount
        if burn_amount == -1: 
            burn_amount = user_token_amount[event.user_index]

        ch: SDKClearingHouse = user_chs[event.user_index]
        await ch.remove_liquidity(
            burn_amount, 
            event.market_index
        )

        user = await get_user_account(
            program, 
            ch.authority, 
        )
        user_baa_amount[event.user_index] = user.positions[0].base_asset_amount
    else: 
        raise NotImplementedError

end_total_collateral = 0 
for (i, ch) in user_chs.items():
    user = await get_user_account(
        program, 
        ch.authority, 
    )

    balance = user.bank_balances[0].balance
    upnl = user.positions[0].unsettled_pnl
    total_user_collateral = balance + upnl

    end_total_collateral += total_user_collateral
    print(i, total_user_collateral)

market = await get_market_account(program, 0)
end_total_collateral += market.amm.total_fee_minus_distributions

print('market:', market.amm.total_fee_minus_distributions)

print(
    "=> difference in $, difference, end/init collateral",
    (end_total_collateral - init_total_collateral) / 1e6, 
    end_total_collateral - init_total_collateral, 
    (end_total_collateral, init_total_collateral)
)

#%%
#%%
#%%
#%%
#%%
#%%