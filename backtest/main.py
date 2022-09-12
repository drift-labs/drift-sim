#%%
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../driftpy/src/')
sys.path.insert(0, './driftpy/src/')

import pandas as pd 
import numpy as np 

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

from driftpy.setup.helpers import _create_usdc_mint, mock_oracle, _airdrop_user, set_price_feed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_usdc_ata_tx
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
from helpers import setup_bank, setup_market, view_logs
from tqdm import tqdm
from driftpy.setup.helpers import _create_user_usdc_ata_tx
from solana.keypair import Keypair

from subprocess import Popen
import os 
import time 
import signal

class LocalValidator:
    def __init__(self, protocol_path) -> None:
        self.protocol_path = protocol_path
        
    def start(self):
        """
        starts a new solana-test-validator by running the given script path 
        and logs the stdout/err to the logfile 
        """

        self.log_file = open('node.txt', 'w')

        process = Popen("anchor build".split(' '), cwd=self.protocol_path)
        process.wait()

        print('starting validator...')
        self.proc = Popen(
            'anchor localnet'.split(' '), 
            stdout=self.log_file, 
            stderr=self.log_file, 
            preexec_fn=os.setsid, 
            cwd=self.protocol_path
        )
        time.sleep(5)

    def stop(self):
        self.log_file.close()
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)  

async def main(protocol_path, experiments_folder):
    # protocol_path = "../driftpy/protocol-v2/"#
    # experiments_folder = 'tmp2'

    val = LocalValidator(protocol_path)
    val.start()

    events = pd.read_csv(f"./{experiments_folder}/events.csv")
    clearing_houses = pd.read_csv(f"./{experiments_folder}/chs.csv")

    workspace = create_workspace(protocol_path)
    program: Program = workspace["clearing_house"]
    oracle_program: Program = workspace["pyth"]
    provider: Provider = program.provider

    clearing_house, usdc_mint = await setup_bank(program)

    # read and load initial clearing house state (thats all we use chs.csv for...)
    init_state = clearing_houses.iloc[0]
    init_reserves = int(init_state.m0_base_asset_reserve) # 200 * 1e13

    oracle = await mock_oracle(workspace["pyth"], 1, -7)
    await clearing_house.initialize_market(
        oracle, 
        int(init_reserves), 
        int(init_reserves), 
        int(60), 
        int(init_state.m0_peg_multiplier), 
        OracleSource.PYTH(), 
    )

    # update durations
    await clearing_house.update_auction_duration(0, 0)
    await clearing_house.update_lp_cooldown_time(0, 0)
    await clearing_house.update_max_base_asset_amount_ratio(1, 0)
    await clearing_house.update_market_base_asset_amount_step_size(1 * AMM_RESERVE_PRECISION, 0)

    # fast init for users - airdrop takes a bit to finalize
    print('airdropping sol to users...')
    user_indexs = np.unique([json.loads(e['parameters'])['user_index'] for _, e in events.iterrows() if 'user_index' in json.loads(e['parameters'])])
    users = {}
    for user_index in tqdm(user_indexs):
        user, tx_sig = await _airdrop_user(provider)
        users[user_index] = (user, tx_sig)

    for i, (user, tx_sig) in tqdm(users.items()):
        await provider.connection.confirm_transaction(tx_sig, sleep_seconds=0.1)

    # process events 
    user_chs = {}
    init_total_collateral = 0 

    for i in tqdm(range(len(events))):
        event = events.iloc[i]

        if event.event_name == DepositCollateralEvent._event_name:
            event = Event.deserialize_from_row(DepositCollateralEvent, event)
            assert event.user_index in users, "user not setup"

            user_index = event.user_index
            user_kp = users[user_index][0]

            # rough draft
            instructions = []
            first_init = user_index not in user_chs
            if first_init: 
                print(f'=> {event.user_index} init user...')
                # initialize user 
                user_clearing_house = SDKClearingHouse(program, user_kp)
                await user_clearing_house.intialize_user()

                usdc_ata_kp = Keypair()
                usdc_ata_tx = await _create_user_usdc_ata_tx(
                    usdc_ata_kp, 
                    provider, 
                    usdc_mint, 
                    user_clearing_house.authority
                )
                user_clearing_house.usdc_ata = usdc_ata_kp
                instructions += usdc_ata_tx.instructions

                user_chs[user_index] = user_clearing_house

            print(f'=> {event.user_index} depositing...')
            user_clearing_house: SDKClearingHouse = user_chs[user_index]

            # add fundings 
            mint_tx = _mint_usdc_tx(
                usdc_mint, 
                provider, 
                event.deposit_amount, 
                user_clearing_house.usdc_ata
            )
            instructions += mint_tx.instructions

            from solana.transaction import Transaction
            tx = Transaction()
            [tx.add(ix) for ix in instructions]
            if first_init:
                await provider.send(tx, [provider.wallet.payer, user_clearing_house.usdc_ata])
            else:
                await provider.send(tx, [provider.wallet.payer])

            # deposit 
            await user_clearing_house.deposit(
                event.deposit_amount, 
                0, 
                user_clearing_house.usdc_ata.public_key, 
            )

            # track collateral 
            init_total_collateral += event.deposit_amount

        elif event.event_name == OpenPositionEvent._event_name: 
            event = Event.deserialize_from_row(OpenPositionEvent, event)
            print(f'=> {event.user_index} opening position...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            await event.run_sdk(ch, oracle_program, adjust_oracle_pre_trade=True)

        elif event.event_name == ClosePositionEvent._event_name: 
            event = Event.deserialize_from_row(ClosePositionEvent, event)
            print(f'=> {event.user_index} closing position...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            await event.run_sdk(ch, oracle_program, adjust_oracle_pre_trade=True)

        elif event.event_name == addLiquidityEvent._event_name: 
            event = Event.deserialize_from_row(addLiquidityEvent, event)
            print(f'=> {event.user_index} adding liquidity...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            await event.run_sdk(ch)

        elif event.event_name == removeLiquidityEvent._event_name:
            event = Event.deserialize_from_row(removeLiquidityEvent, event)
            print(f'=> {event.user_index} removing liquidity...')
            assert event.user_index in user_chs, 'user doesnt exist'
            event.lp_token_amount = -1

            ch: SDKClearingHouse = user_chs[event.user_index]
            await event.run_sdk(ch)

        elif event.event_name == SettleLPEvent._event_name: 
            event = Event.deserialize_from_row(SettleLPEvent, event)
            print(f'=> {event.user_index} settle lp...')
            ch: SDKClearingHouse = user_chs[event.user_index]
            await event.run_sdk(ch)
        
        elif event.event_name == NullEvent._event_name: 
            pass
        else: 
            raise NotImplementedError

    # compute total collateral at end of sim
    end_total_collateral = 0 
    for (i, ch) in user_chs.items():
        user = await get_user_account(
            program, 
            ch.authority, 
        )

        balance = user.bank_balances[0].balance
        position = await ch.get_user_position(0)
        upnl = position.quote_asset_amount
        total_user_collateral = balance + upnl

        print(
            f'user {i}', 
            user.positions[0].base_asset_amount, 
            user.positions[0].lp_shares,
            user.positions[0].remainder_base_asset_amount           
        )
        end_total_collateral += total_user_collateral

    market = await get_market_account(program, 0)
    market_collateral = 0 # market.amm.market_position.quote_asset_amount
    market_collateral += market.amm.total_fee_minus_distributions
    end_total_collateral += market_collateral 

    print('market:', market_collateral)
    print(
        "=> difference in $, difference, end/init collateral",
        (end_total_collateral - init_total_collateral) / 1e6, 
        end_total_collateral - init_total_collateral, 
        (end_total_collateral, init_total_collateral)
    )

    print(
        "net baa & net unsettled:",
        market.amm.net_base_asset_amount, 
        market.amm.net_unsettled_lp_base_asset_amount,
        market.amm.net_base_asset_amount + market.amm.net_unsettled_lp_base_asset_amount
    )

    # stop the validator
    val.stop()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=str)
    parser.add_argument('--protocol', type=str)
    args = parser.parse_args()

    import asyncio
    asyncio.run(main(args.protocol, args.events))

# %%
# %%
# %%
