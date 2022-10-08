import pandas as pd 
import numpy as np 

from solana.rpc import commitment
from solana.keypair import Keypair

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

from driftpy.setup.helpers import _create_usdc_mint, mock_oracle, _airdrop_user, set_price_feed, adjust_oracle_pretrade
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.math.amm import calculate_mark_price_amm

from anchorpy import Provider, Program, create_workspace, WorkspaceType
from programs.clearing_house.state.market import SimulationAMM, SimulationMarket
import pprint

async def setup_market(
    clearing_house: Admin,
    market: SimulationMarket,
    workspace: WorkspaceType
):
    amm = market.amm
    oracle = await mock_oracle(workspace["pyth"], 1, -7)

    await clearing_house.initialize_market(
        oracle, 
        int(amm.base_asset_reserve), 
        int(amm.quote_asset_reserve), 
        int(amm.funding_period), 
        int(amm.peg_multiplier), 
        OracleSource.Pyth(), 
    )

    # update durations
    await clearing_house.update_auction_duration(0, 0)
    await clearing_house.update_lp_cooldown_time(0, 0)
    await clearing_house.update_max_base_asset_amount_ratio(1, 0)
    await clearing_house.update_perp_step_size_and_tick_size(0, 1, 1)
    
    # add a spread 
    if amm.base_spread > 0:
        print('setting spread..')
        await clearing_house.update_market_base_spread(amm.base_spread, 0)

    return oracle

async def setup_bank(
    program: Program,
):
    # init usdc mint
    usdc_mint = await _create_usdc_mint(program.provider)

    # init state + bank + market 
    clearing_house = Admin(program)
    await clearing_house.initialize(usdc_mint.public_key, True)
    await clearing_house.initialize_spot_market(usdc_mint.public_key)

    return clearing_house, usdc_mint

async def view_logs(
    sig,
    provider: Provider
):
    provider.connection._commitment = commitment.Confirmed 
    try: 
        await provider.connection.confirm_transaction(sig, commitment.Confirmed)
        logs = (await provider.connection.get_transaction(sig))["result"]["meta"]["logMessages"]
    finally:
        provider.connection._commitment = commitment.Processed 
    pprint.pprint(logs)