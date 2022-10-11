#%%
%load_ext autoreload
%autoreload 2

import sys
sys.path.insert(0, './driftpy/src/')

import driftpy
print(driftpy.__path__)

from driftpy.types import User
from driftpy.constants.config import configs
from anchorpy import Provider
import json 
from anchorpy import Wallet
from solana.rpc.async_api import AsyncClient
from driftpy.clearing_house import ClearingHouse
from driftpy.accounts import *
from driftpy.constants.numeric_constants import * 
from solana.publickey import PublicKey
from dataclasses import asdict
from solana.keypair import Keypair
import asyncio
import pathlib 
from tqdm.notebook import tqdm 

# random key 
with open('../pydrift/tmp.json', 'r') as f: secret = json.load(f) 
kp = Keypair.from_secret_key(bytes(secret))
print('pk:', kp.public_key)

# todo: airdrop udsc + init account for any kp
# rn do it through UI 

# %%
config = configs['devnet']
url = 'https://api.devnet.solana.com'
wallet = Wallet(kp)
connection = AsyncClient(url)
provider = Provider(connection, wallet)
ch = ClearingHouse.from_config(config, provider)
from driftpy.clearing_house_user import ClearingHouseUser
pubkey = PublicKey("HCQVSVwDpcudiWzdz6BrgNGEZYtgczN9ErT59Yo7gV9k")
chu = ClearingHouseUser(ch, pubkey)

#%%
user = await chu.get_user_account()
bt = user.spot_positions[0].scaled_balance / QUOTE_PRECISION
f"{bt:,.0f}"

#%%
await chu.can_be_liquidated()

#%%
user = await chu.get_user_account()
position = user.spot_positions[0]
spot_market = await get_spot_market_account(
    chu.program, 0
)
spot_token_value = get_token_amount(
    position.balance, 
    spot_market, 
    position.balance_type
)
spot_token_value 

#%%
col = await chu.get_total_collateral()
f"{col / QUOTE_PRECISION:,.0f}"

#%%
position = await chu.get_user_position(0)
market = await get_perp_market_account(
    chu.program, 
    position.market_index
)
oracle_data = await get_oracle_data(market.amm.oracle)

pnl = calculate_position_pnl(market, position, oracle_data, True)
pnl / QUOTE_PRECISION

#%%
init_margin = await chu.get_margin_requirement(
    MarginCategory.INITIAL
)
f"{init_margin / QUOTE_PRECISION:,.0f}"

#%%
free = await chu.get_free_collateral()
f"{free / QUOTE_PRECISION:,.0f}"

#%%
from driftpy.clearing_house_user import * 
base_value = calculate_base_asset_value_with_oracle(position, oracle_data)
base_asset_sign = -1 if position.base_asset_amount < 0 else 1
pnl = base_value * base_asset_sign + position.quote_asset_amount
pnl / QUOTE_PRECISION

#%%
await chu.get_leverage() / 10_000

#%%
spot_market = await get_spot_market_account(
    ch.program, 
    1
)
spot_market.oracle

#%%
from driftpy.clearing_house_user import ClearingHouseUser
chu = ClearingHouseUser(ch)
await chu.get_spot_market_asset_value(include_open_orders=True, margin_category="Initial")

#%%
await chu.get_spot_market_asset_value(include_open_orders=True, margin_category=None)

#%%
#%%
#%%
#%%
#%%

