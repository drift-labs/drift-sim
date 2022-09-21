#%%
import sys
sys.path.insert(0, './driftpy/src/')

import driftpy
print(driftpy.__path__)

from driftpy.constants import * 
from anchorpy import Provider, Program, create_workspace

## note first run `anchor localnet` in v2 dir

path = './driftpy/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
provider: Provider = program.provider

#%%
from driftpy.accounts import *

market = await get_market_account(program, 0)

#%%
if market.amm.net_base_asset_amount < 0: # users short (after close out = will add quote to pool)
    print('u')
    print(
        market.amm.quote_asset_reserve < market.amm.terminal_quote_asset_reserve
    )
    print(
        market.amm.quote_asset_reserve , market.amm.terminal_quote_asset_reserve
    )

#%%
market.amm.user_lp_shares / market.amm.sqrt_k

#%%


#%%
from solana.publickey import PublicKey
pk = PublicKey('ComputeBudget111111111111111111111111111111')
pk

#%%
from construct import Struct as CStruct
from construct import Int64ub as U32

request_units = CStruct(
    "units" / U32, 
    "additional_fee" / U32
)

#%%
from solana.transaction import TransactionInstruction, Transaction

tx = Transaction()
ix = TransactionInstruction(
    [], 
    pk, 
    request_units.build({"units": 500000, "additional_fee": int(0.01*10**9)})
)
tx.add(ix)

from solana.rpc.commitment import Confirmed
provider.connection._commitment = Confirmed 

sig = await provider.send(tx)
resp = await provider.connection.get_transaction(sig)
resp

#%%
#%%
#%%
#%%
#%%
#%%

