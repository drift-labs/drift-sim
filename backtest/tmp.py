
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

import pprint
async def view_logs(sig):
    from solana.rpc import commitment
    provider.connection._commitment = commitment.Confirmed 
    try: 
        await provider.connection.confirm_transaction(sig, commitment.Confirmed)
        logs = (await provider.connection.get_transaction(sig))["result"]["meta"]["logMessages"]
    finally:
        provider.connection._commitment = commitment.Processed 
    pprint.pprint(logs)

async def setup_new_user(
    deposit_amount = 1_000_000_000 * QUOTE_PRECISION
):
    print('init user...')
    user_keypair = await _setup_user(provider) 
    user_clearing_house = SDKClearingHouse(program, user_keypair)
    usdc_kp = await _user_usdc_account(
        usdc_mint, 
        provider, 
        deposit_amount, 
        owner=user_keypair.public_key
    )
    await user_clearing_house.intialize_user()
    await user_clearing_house.deposit(deposit_amount, 0, usdc_kp.public_key)

    return user_clearing_house, deposit_amount

#%%
# run `anchor localnet` in v2 dir first 
path = '../driftpy/protocol-v2'
path = '/Users/brennan/Documents/drift/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
oracle_program: Program = workspace["pyth"]
provider: Provider = program.provider

async def setup_bank():
    # init usdc mint
    usdc_mint = await _usdc_mint(provider)

    # init state + bank + market 
    clearing_house = Admin(program)
    await clearing_house.initialize(usdc_mint.public_key, True)
    await clearing_house.initialize_bank(usdc_mint.public_key)

    return clearing_house, usdc_mint

clearing_house, usdc_mint = await setup_bank()

#%%
async def setup_market(
    clearing_house: Admin,
    market: SimulationMarket
):
    amm = market.amm
    # init_price = round(amm.peg_multiplier / np.log10(PEG_PRECISION), 3)
    # oracle = await mock_oracle(workspace["pyth"], init_price, -int(np.log10(PEG_PRECISION)))

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

    return oracle

init_reserves = 200 * 1e13
init_market = SimulationMarket(
    market_index=0,
    amm=SimulationAMM(
        oracle=None,
        base_asset_reserve=init_reserves, 
        quote_asset_reserve=init_reserves, 
        funding_period = 60 * 60, # 1 hour dont worry about funding updates for now 
        peg_multiplier=1 * PEG_PRECISION,
    )
)
oracle = await setup_market(clearing_house, init_market)

#%%
## trader
init_collateral = 2 * 1_000_000_000 * QUOTE_PRECISION
trader_ch = await setup_new_user()
lp_ch = await setup_new_user()

#%%
lp_tokens = int(100 * 1e13)
sig = await lp_ch.add_liquidity(
    lp_tokens, 
    0
)
lp = await get_user_account(
    program, lp_ch.authority
)
print(
    lp.positions[0].lp_shares
)
lp_ratio = lp_tokens / (init_reserves + lp_tokens)
lp_ratio

#%%
baa = int(124 * 1e13)
direction = PositionDirection.LONG()
# market = await get_market_account(program, 0)
market = init_market

await adjust_oracle_pretrade(
    baa, 
    direction, 
    market, 
    oracle,
    oracle_program
)
sig = await trader_ch.open_position(
    direction, 
    baa,
    0, 
    int(100 * 1e13)
)
await view_logs(sig)

#%%
trader = await get_user_account(program, trader_ch.authority)
print(
    "trader pos"
    trader.positions[0].base_asset_amount, 
    trader.positions[0].quote_asset_amount
)

#%%
#%%
sig = await lp_ch.remove_liquidity(lp_tokens, 0)
await view_logs(sig)

#%%
await trader_ch.close_position(0)
await lp_ch.close_position(0)

#%%
trader = await get_user_account(
    program, 
    trader_ch.authority
)
lp = await get_user_account(
    program, 
    lp_ch.authority
)

total_collateral = 0

# users
for name,user in zip(["trader", "lp"], [trader, lp]):
    balance = user.bank_balances[0].balance
    pnl = user.positions[0].unsettled_pnl
    print(name, pnl)
    total_collateral += balance + pnl

# market 
market = await get_market_account(
    program, 0
)
print('market', market.amm.total_fee_minus_distributions)
total_collateral += market.amm.total_fee_minus_distributions

total_collateral, init_collateral

#%%