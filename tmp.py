#%%
import sys
sys.path.insert(0, './driftpy/src/')

import driftpy
print(driftpy.__path__)

from programs.clearing_house.state.market import Oracle, SimulationAMM, SimulationMarket
from sim.helpers import random_walk_oracle
from driftpy.constants import * 
from anchorpy import Provider, Program, create_workspace

## note first run `anchor localnet` in v2 dir

path = '../driftpy/protocol-v2'
workspace = create_workspace(path)
program: Program = workspace["clearing_house"]
provider: Provider = program.provider

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

