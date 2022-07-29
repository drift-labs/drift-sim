
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
# run `anchor localnet` in v2 dir first 
path = '../driftpy/protocol-v2'
path = '/Users/brennan/Documents/drift/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
oracle_program: Program = workspace["pyth"]
provider: Provider = program.provider

clearing_house, usdc_mint = await setup_bank(
    program
)

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
oracle = await setup_market(clearing_house, init_market, workspace)

#%%
## trader
init_collateral = 0 

trader_ch, collateral = await setup_new_user(
    provider, 
    program, 
    usdc_mint, 
)
init_collateral += collateral

lp_ch, collateral = await setup_new_user(
    provider, 
    program, 
    usdc_mint, 
)
init_collateral += collateral

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
await view_logs(sig, provider)

#%%
trader = await get_user_account(program, trader_ch.authority)
print(
    "trader pos",
    trader.positions[0].base_asset_amount, 
    trader.positions[0].quote_asset_amount
)

#%%
sig = await lp_ch.remove_liquidity(lp_tokens, 0)
await view_logs(sig, provider)

#%%
for _ in range(2):
    await trader_ch.close_position(0)

#%%
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

trader_position = trader.positions[0]
lp_position = lp.positions[0]

print(
    "trader pos",
    trader.positions[0].base_asset_amount, 
    trader.positions[0].quote_asset_amount,
)
print(
    "lp pos",
    lp.positions[0].base_asset_amount, 
    lp.positions[0].quote_asset_amount,
)

#%%
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