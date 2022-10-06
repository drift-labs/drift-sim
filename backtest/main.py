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
from driftpy.types import PerpMarket
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
            preexec_fn=os.setsid, 
            cwd=self.protocol_path
        )
        time.sleep(5)

    def stop(self):
        self.log_file.close()
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)  

from driftpy.clearing_house_user import ClearingHouseUser

async def init_user(
    user_chs,
    user_chus,
    user_index, 
    program, 
    usdc_mint, 
    provider,
    deposit_amount, 
    user_kp
):
    # rough draft
    instructions = []

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
    user_chus[user_index] = ClearingHouseUser(user_clearing_house)

    # add fundings 
    mint_tx = _mint_usdc_tx(
        usdc_mint, 
        provider, 
        deposit_amount, 
        user_clearing_house.usdc_ata
    )
    instructions += mint_tx.instructions

    instructions += [
        await user_clearing_house.get_deposit_collateral_ix(
            deposit_amount, 
            0, 
            user_clearing_house.usdc_ata.public_key
        )
    ]

    from solana.transaction import Transaction
    tx = Transaction()
    [tx.add(ix) for ix in instructions]
    routine = provider.send(tx,  user_clearing_house.signers + [provider.wallet.payer, user_clearing_house.usdc_ata])

    return await routine

async def main(protocol_path, experiments_folder):
    # e.g.
    # protocol_path = "../driftpy/protocol-v2/"#
    # experiments_folder = 'tmp2'
    events = pd.read_csv(f"./{experiments_folder}/events.csv")
    clearing_houses = pd.read_csv(f"./{experiments_folder}/chs.csv")

    workspace = create_workspace(protocol_path)
    program: Program = workspace["clearing_house"]
    oracle_program: Program = workspace["pyth"]
    provider: Provider = program.provider

    admin_clearing_house, usdc_mint = await setup_bank(program)

    # read and load initial clearing house state (thats all we use chs.csv for...)
    init_state = clearing_houses.iloc[0]
    init_reserves = int(init_state.m0_base_asset_reserve) / 1e13 * AMM_RESERVE_PRECISION # 200 * 1e13
    print('> initial reserves:', init_reserves)
    print('> initial reserves log:', np.log10(init_reserves))

    print('> init peg', init_state.m0_peg_multiplier / PEG_PRECISION)
    oracle = await mock_oracle(workspace["pyth"], init_state.m0_peg_multiplier / PEG_PRECISION, -7)
    init_leverage = 11
    await admin_clearing_house.initialize_market(
        oracle, 
        int(init_reserves), 
        int(init_reserves), 
        int(60), 
        int(init_state.m0_peg_multiplier), 
        OracleSource.PYTH(), 
        # default is 5x
        margin_ratio_initial=MARGIN_PRECISION // init_leverage if init_leverage else 2000
    )

    # update durations
    await admin_clearing_house.update_perp_auction_duration(0)
    await admin_clearing_house.update_lp_cooldown_time(0, 0)
    await admin_clearing_house.update_max_base_asset_amount_ratio(1, 0)
    await admin_clearing_house.update_market_base_asset_amount_step_size(1 * AMM_RESERVE_PRECISION, 0)

    # fast init for users - airdrop takes a bit to finalize
    print('airdropping sol to users...')
    user_indexs = np.unique([json.loads(e['parameters'])['user_index'] for _, e in events.iterrows() if 'user_index' in json.loads(e['parameters'])])
    user_indexs = list(np.sort(user_indexs))

    liquidator_index = user_indexs[-1] + 1
    user_indexs.append(liquidator_index) # liquidator

    users = {}
    for user_index in tqdm(user_indexs):
        user, tx_sig = await _airdrop_user(provider)
        users[user_index] = (user, tx_sig)

    for i, (user, tx_sig) in tqdm(users.items()):
        await provider.connection.confirm_transaction(tx_sig, sleep_seconds=0.1)

    # process events 
    user_chs = {}
    user_chus = {}
    init_total_collateral = 0 

    import time 
    start = time.time()

    # deposit all at once for speed 
    deposit_amounts = {}
    for i in tqdm(range(len(events))):
        event = events.iloc[i]

        if event.event_name == DepositCollateralEvent._event_name:
            event = Event.deserialize_from_row(DepositCollateralEvent, event)
            deposit_amounts[event.user_index] = deposit_amounts.get(event.user_index, 0) + event.deposit_amount

            # track market state after event
            market: PerpMarket = await get_market_account(program, 0)
            d = market.amm.__dict__
            d.pop("padding")
            if i > 0:
                pd.DataFrame(d, index=[0]).to_csv(f"./{experiments_folder}/result_market0.csv",
                    mode="a", index=False, header=False
                )
            else:
                pd.DataFrame(d, index=[0]).to_csv(f"./{experiments_folder}/result_market0.csv", index=False)

    deposit_amounts[liquidator_index] = 1_000_000 * QUOTE_PRECISION

    routines = [] 
    for user_index in deposit_amounts.keys(): 
        deposit_amount = deposit_amounts[user_index]
        user_kp = users[user_index][0]
        print(f'=> user {user_index} depositing {deposit_amount / QUOTE_PRECISION:,.0f}...')

        routine = init_user(
            user_chs,
            user_chus,
            user_index, 
            program, 
            usdc_mint, 
            provider,
            deposit_amount, 
            user_kp
        )
        routines.append(routine)

        # track collateral 
        init_total_collateral += deposit_amount

    await asyncio.gather(*routines)

    liquidator_clearing_house: ClearingHouse = user_chs[liquidator_index]

    async def try_liquidate():
        ch: ClearingHouse
        promises = []
        for ch in user_chs.values(): 
            authority = ch.authority
            if authority == liquidator_clearing_house.authority: 
                continue
            position = await ch.get_user_position(0)
            if position and position.base_asset_amount != 0:
                promise = liquidator_clearing_house.liquidate_perp(
                    authority, 
                    0,
                    abs(position.base_asset_amount) # take it fully on
                )
                promises.append(promise)

        for promise in promises:
            try:
                await promise
                from termcolor import colored
                print(colored('     *** liquidation successful ***   ', "green"))
            except Exception as e:
                if "0x1774" in e.args[0]['message']: # sufficient collateral
                    continue 
                elif "0x1793" in e.args[0]['message']: # invalid oracle
                    continue 
                else: 
                    raise Exception(e)

        await derisk()
        await resolve_bankruptcies()

    async def resolve_bankruptcies():
        ch: ClearingHouse
        user_promises = []
        for ch in user_chs.values(): 
            authority = ch.authority
            if authority == liquidator_clearing_house.authority: 
                continue
            user = ch.get_user()
            user_promises.append(user)
        users = await asyncio.gather(*user_promises)
        promises = []
        user: User
        for user in users:
            if user.bankrupt:
                promise = liquidator_clearing_house.resolve_perp_bankruptcy(
                    authority,  0
                )
                promises.append(promise)

        for promise in promises:
            await promise
            from termcolor import colored
            print(colored('     *** bankrupt resolved ***   ', "green"))
        
    async def derisk():
        ch = liquidator_clearing_house
        position = await ch.get_user_position(0)
        if position is None or position.base_asset_amount == 0: 
            return
        print(f'=> liquidator derisking {position.base_asset_amount} baa')
        await ch.close_position(0)

    # todo 
    #   calculate margin requirements of user same as js sdk 

    df_rows = {}
    for i in tqdm(range(len(events))):
        event = events.iloc[i]

        if event.event_name == DepositCollateralEvent._event_name:
            continue

        elif event.event_name == OpenPositionEvent._event_name: 
            event = Event.deserialize_from_row(OpenPositionEvent, event)
            print(f'=> {event.user_index} opening position...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            sig = await event.run_sdk(ch, init_leverage, oracle_program, adjust_oracle_pre_trade=True)

        elif event.event_name == ClosePositionEvent._event_name: 
            # dont close so we have stuff to settle 
            continue
            # event = Event.deserialize_from_row(ClosePositionEvent, event)
            # print(f'=> {event.user_index} closing position...')
            # assert event.user_index in user_chs, 'user doesnt exist'
            
            # ch: SDKClearingHouse = user_chs[event.user_index]
            # await event.run_sdk(ch, oracle_program, adjust_oracle_pre_trade=True)

        elif event.event_name == addLiquidityEvent._event_name: 
            event = Event.deserialize_from_row(addLiquidityEvent, event)
            print(f'=> {event.user_index} adding liquidity: {event.token_amount}...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            # todo: update old percisions from backtest folders
            event.token_amount = int(event.token_amount * AMM_RESERVE_PRECISION / 1e13)
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
        
        elif event.event_name == oraclePriceEvent._event_name: 
            event = Event.deserialize_from_row(oraclePriceEvent, event)
            print(f'=> adjusting oracle: {event.price}')
            await event.run_sdk(program, oracle_program)

        elif event.event_name == 'liquidate':
            print('=> liquidating...')
            await try_liquidate()
        
        elif event.event_name == NullEvent._event_name: 
            continue
        
        #
        await try_liquidate()

        # track market state after event
        market: PerpMarket = await get_market_account(program, 0)
        d = market.amm.__dict__
        d.pop("padding")
        if i > 0:
            pd.DataFrame(d, index=[0]).to_csv(f"./{experiments_folder}/result_market0.csv",
                mode="a", index=False, header=False
            )
        else:
            pd.DataFrame(d, index=[0]).to_csv(f"./{experiments_folder}/result_market0.csv", index=False)

        # # track metrics
        # chu: ClearingHouseUser
        # leverages = []
        # indexs = []
        # for user_index, chu in user_chus.items():
        #     leverage = chu.get_leverage()
        #     leverages.append(leverage)
        #     indexs.append(user_index)
        
        # leverages = await asyncio.gather(*leverages)
        # for l, i in zip(leverages, indexs):
        #     k = f"user_{i}"
        #     df_rows[k] = df_rows.get(k, []) + [l / 10_000]

    print('delisting market...')
    # get
    slot = (await provider.connection.get_slot())['result']
    time: int = (await provider.connection.get_block_time(slot))['result']

    # + N seconds
    seconds_time = 2
    await admin_clearing_house.update_market_expiry(time + seconds_time, 0)
    
    # close out all the LPs 
    routines = []
    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is None: 
            continue
        if position.lp_shares > 0:
            print(f'removing {position.lp_shares} lp shares...')
            routines.append(
                ch.remove_liquidity(position.lp_shares, position.market_index)
            )
    await asyncio.gather(*routines)

    # settle expired market
    import time 
    time.sleep(seconds_time)
    sig = await admin_clearing_house.settle_expired_market(0)

    market = await get_market_account(
        program, 0
    )
    print(
        'market settlment price vs twap', 
        market.settlement_price, 
        market.amm.historical_oracle_data.last_oracle_price_twap
    )

    # liquidate em + resolve bankrupts
    await try_liquidate()

    # cancel open orders
    routines = []
    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is not None and position.open_orders > 0:
            routines.append(
                ch.cancel_order()
            )
    await asyncio.gather(*routines)

    # settle expired positions 
    print('settling expired positions')

    number_positions = 0
    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is None: 
            continue
        number_positions += 1
    print('number of positions:', number_positions)

    market = await get_market_account(program, 0)
    print(
        'net long/short',
        market.base_asset_amount_long, 
        market.base_asset_amount_short, 
        market.open_interest, 
    )

    from termcolor import colored
    routines = []
    success = False
    attempt = -1
    user_count = 0
    n_users = len(list(user_chs.keys()))
    while not success:
        attempt += 1
        success = True
        print(f'attempt {attempt}')
        for (i, ch) in user_chs.items():
            position = await ch.get_user_position(0)
            if position is None: 
                user_count += 1
                continue

            try:
                await ch.settle_expired_position(ch.authority, 0)
                user_count += 1
                print(colored(f'     *** settle expired position successful {user_count}/{n_users} ***   ', "green"))
            except Exception as e:
                if "0x17e2" in e.args[0]['message']: # pool doesnt have enough 
                    print(colored(f'     *** settle expired position failed... ***   ', "red"))
                    print(e.args)
                    success = False
                else: 
                    raise Exception(e)

            market = await get_market_account(program, 0)
            print(
                'net long/short',
                market.base_asset_amount_long, 
                market.base_asset_amount_short, 
                market.open_interest, 
            )

    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is None: 
            continue
        print(position)

    await admin_clearing_house.settle_expired_market_pools_to_revenue_pool(0)

    market = await get_market_account(
        program, 0
    )
    print(market.status)

    # df = pd.DataFrame(df_rows)
    # df.to_csv('tmp.csv', index=False)

    # # close out anyone who hasnt already closed out 
    # print('closing out everyone...')
    # net_baa = 1 
    # market = await get_market_account(program, 0)
    # max_n_tries = 4
    # n_tries = 0
    # while net_baa != 0 and n_tries < max_n_tries:
    #     n_tries += 1
    #     net_baa = 0
    #     for (i, ch) in tqdm(user_chs.items()):
    #         position = await ch.get_user_position(0)
    #         if position is None: 
    #             continue
    #         net_baa += abs(position.base_asset_amount)

    #         if position.lp_shares > 0:
    #             await ch.remove_liquidity(position.lp_shares, position.market_index)
    #             position = await ch.get_user_position(0)

    #         if position.base_asset_amount != 0: 
    #             await ch.close_position(position.market_index)

    # compute total collateral at end of sim
    end_total_collateral = 0 
    for (i, ch) in user_chs.items():
        user = await get_user_account(
            program, 
            ch.authority, 
        )
        balance = user.spot_positions[0].balance / SPOT_BALANCE_PRECISION * QUOTE_PRECISION
        position = await ch.get_user_position(0)

        if position is None: 
            end_total_collateral += balance
            continue

        upnl = position.quote_asset_amount
        total_user_collateral = balance + upnl

        print(
            f'user {i}  :', 
            user.perp_positions[0].base_asset_amount, 
            user.perp_positions[0].quote_asset_amount, 
            total_user_collateral
        )
        end_total_collateral += total_user_collateral

    print('---')

    market = await get_market_account(program, 0)
    market_collateral = 0 
    market_collateral += market.amm.total_fee_minus_distributions
    end_total_collateral += market_collateral 

    print('market $:', market_collateral)
    print(f'difference in $ {(end_total_collateral - init_total_collateral) / QUOTE_PRECISION:,}')
    print(
        "=> end/init collateral",
        (end_total_collateral, init_total_collateral)
    )

    print(
        "net baa & net unsettled:",
        market.amm.market_position.base_asset_amount,
        market.amm.net_base_asset_amount, 
        market.amm.net_unsettled_lp_base_asset_amount,
        market.amm.net_base_asset_amount + market.amm.net_unsettled_lp_base_asset_amount
    )

    print(
        'net long/short',
        market.base_asset_amount_long, 
        market.base_asset_amount_short, 
        market.amm.user_lp_shares, 
    )

    print(
        'total time (seconds):',
        time.time() - start
    )


    await provider.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=str, required=True)
    parser.add_argument('--protocol', type=str, required=True)
    args = parser.parse_args()

    val = LocalValidator(args.protocol)
    val.start()
    try: 
        import asyncio
        asyncio.run(main(args.protocol, args.events))
    finally:
        # pass
        val.stop()

# %%
