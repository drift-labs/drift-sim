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

from driftpy.setup.helpers import _usdc_mint, _user_usdc_account, mock_oracle, _setup_user
from driftpy.clearing_house import ClearingHouse
from driftpy.admin import Admin
from driftpy.types import OracleSource

from programs.clearing_house.state.market import SimulationAMM, SimulationMarket

#%%
events = pd.read_csv("../sim-results/tmp/events.csv")
clearing_houses = pd.read_csv("../sim-results/tmp/chs.csv")
clearing_houses.head()

#%%
## setup clearing house + bank + market 
from anchorpy import Provider, Program, create_workspace

## note first run `anchor localnet` in v2 dir

path = '../driftpy/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
provider: Provider = program.provider

#%%
async def setup(init_market: SimulationMarket):
    # init usdc mint
    usdc_mint = await _usdc_mint(provider)

    # init state + bank + market 
    clearing_house = Admin(program)
    try:
        await clearing_house.initialize(usdc_mint.public_key, True)
        await clearing_house.initialize_bank(usdc_mint.public_key)
    except Exception:
        print('initiz failed')
        pass

    amm = init_market.amm
    init_price = round(amm.peg_multiplier / np.log10(PEG_PRECISION), 3)
    oracle = await mock_oracle(workspace["pyth"], init_price, -int(np.log10(PEG_PRECISION)))
    await clearing_house.initialize_market(
        oracle, 
        int(amm.base_asset_reserve), 
        int(amm.quote_asset_reserve), 
        int(amm.funding_period), 
        int(amm.peg_multiplier), 
        OracleSource.Pyth(), 
    )

    return usdc_mint

init_state = clearing_houses.iloc[0]
init_market = SimulationMarket(
    market_index=0,
    amm=SimulationAMM(
        oracle=None,
        base_asset_reserve=int(init_state.m0_base_asset_reserve), 
        quote_asset_reserve=int(init_state.m0_quote_asset_reserve), 
        funding_period=int(init_state.m0_funding_period), 
        peg_multiplier=int(init_state.m0_peg_multiplier),
    )
)
usdc_mint = await setup(init_market)

#%%
from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.accounts import get_market_account
from driftpy.math.amm import calculate_mark_price_amm

user_chs = {}
user_token_amount = {}

for i in range(len(events)):
    event = events.iloc[i]
    if event.event_name == DepositCollateralEvent._event_name:
        event = Event.deserialize_from_row(DepositCollateralEvent, event)
        assert event.user_index not in user_chs, 'trying to re-init'
        print(f'{event.user_index} init user...')

        user = await _setup_user(provider)
        user_clearing_house = SDKClearingHouse(program, user)

        usdc_kp = await _user_usdc_account(
            usdc_mint, 
            provider, 
            event.deposit_amount, 
            owner=user.public_key
        )
        await user_clearing_house.intialize_user()
        await user_clearing_house.deposit(event.deposit_amount, 0, usdc_kp.public_key)
        
        user_chs[event.user_index] = user_clearing_house

    elif event.event_name == OpenPositionEvent._event_name: 
        event = Event.deserialize_from_row(OpenPositionEvent, event)
        print(f'{event.user_index} opening position...')
        assert event.user_index in user_chs, 'user doesnt exist'

        market = await get_market_account(program, 0)
        mark_price = calculate_price(
            market.amm.base_asset_reserve,
            market.amm.quote_asset_reserve,
            market.amm.peg_multiplier,
        )
        baa = int(event.quote_amount * AMM_RESERVE_PRECISION / QUOTE_PRECISION / mark_price)

        ch: SDKClearingHouse = user_chs[event.user_index]
        await ch.open_position(
            PositionDirection.LONG() if event.direction == 'long' else PositionDirection.SHORT(), 
            baa, 
            event.market_index
        )

    elif event.event_name == ClosePositionEvent._event_name: 
        event = Event.deserialize_from_row(ClosePositionEvent, event)
        print(f'{event.user_index} closing position...')
        assert event.user_index in user_chs, 'user doesnt exist'

        ch: SDKClearingHouse = user_chs[event.user_index]
        ch.close_position(event.market_index)

    elif event.event_name == addLiquidityEvent._event_name:
        event = Event.deserialize_from_row(addLiquidityEvent, event)
        print(f'{event.user_index} adding liquidity...')
        assert event.user_index in user_chs, 'user doesnt exist'

        ch: SDKClearingHouse = user_chs[event.user_index]
        user_token_amount[event.user_index] = event.token_amount
        await ch.add_liquidity(
            event.token_amount, 
            event.market_index
        )

    elif event.event_name == removeLiquidityEvent._event_name:
        event = Event.deserialize_from_row(removeLiquidityEvent, event)
        print(f'{event.user_index} removing liquidity...')
        assert event.user_index in user_chs, 'user doesnt exist'

        burn_amount = event.lp_token_amount
        if burn_amount == -1: 
            burn_amount = user_token_amount[event.user_index]

        ch: SDKClearingHouse = user_chs[event.user_index]
        await ch.remove_liquidity(
            burn_amount, 
            event.market_index
        )

#%%