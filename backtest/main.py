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
from driftpy.types import PerpMarket
from driftpy.constants.numeric_constants import *

from driftpy.setup.helpers import _create_mint, mock_oracle, _airdrop_user, set_price_feed, set_price_feed_detailed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_ata_tx
from driftpy.clearing_house import ClearingHouse
from driftpy.admin import Admin
from driftpy.types import OracleSource
from driftpy.clearing_house_user import get_token_amount as sdk_token_amount

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account
from driftpy.math.amm import calculate_mark_price_amm

from anchorpy import Provider, Program, create_workspace, close_workspace
from sim.driftsim.clearing_house.state.market import SimulationAMM, SimulationMarket
from tqdm import tqdm
from driftpy.setup.helpers import _create_user_ata_tx
from driftpy.clearing_house_user import ClearingHouseUser
from solana.keypair import Keypair

from termcolor import colored
from subprocess import Popen
import time 
from solana.transaction import TransactionInstruction

from .parsing import *
from .helpers import *
from .setup import *
from .liquidator import Liquidator
from solana.rpc.core import RPCException
from anchorpy.coder.common import _sighash
import re 

# set inside run_trail()
LOGGER: Logger = None

async def _send_ix(
    ch: ClearingHouse, 
    ix: TransactionInstruction, 
    event_name: str, 
    ix_args: dict, 
    silent_fail=False, 
    silent_success=False,
    view_logs_flag=False,
):
    failed = 1 # 1 = fail, 0 = success
    provider: Provider = ch.program.provider
    slot = (await provider.connection.get_slot())['result']
    compute_used = -1
    err = None
    sig = None
    logs = None
    try:
        if event_name == SettleLPEvent._event_name:
            sig = await ch.send_ixs(ix, signers=[])
        else:
            sig = await ch.send_ixs(ix)
        failed = 0
        if view_logs_flag:
            logs = view_logs(sig, provider, False)

    except RPCException as e:
        err = e.args
    
    if not failed and not silent_success: 
        print(colored(f'> {event_name} success', "green"))
    elif failed and not silent_fail or view_logs_flag:
        print(colored(f'> {event_name} failed', "red"))
        pprint.pprint(ix_args)
        pprint.pprint(err)

    if logs: 
        try:
            logs = await logs
            if view_logs_flag:
                pprint.pprint(logs)
            for log in logs:
                if 'compute units' in log: 
                    result = re.search(r'.* consumed (\d+) of (\d+)', log)
                    compute_used = result.group(1)
        except Exception as e:
            pprint.pprint(e)

    ix_args['user_index'] = ch.user_index
    
    return failed, sig, (slot, event_name, ix_args, err, compute_used)
    
async def send_ix(
    ch: ClearingHouse, 
    ix: TransactionInstruction, 
    event_name: str, 
    ix_args: dict, 
    silent_fail=False, 
    silent_success=False,
    view_logs_flag=False,
):
    global LOGGER
    global args

    failed, sig, log_args = _send_ix(
        ch, 
        ix, 
        event_name, 
        ix_args, 
        silent_fail, 
        silent_success,
        view_logs_flag or not args.ignore_compute,
    )
    LOGGER.log(*log_args)
    return failed

async def run_trial(
    protocol_path,
    events, 
    markets, 
    spot_markets,
    trial_outpath, 
    state_path,
    user_path,
    oracle_guard_rails=None, 
    spread=None
):
    print('trial_outpath:', trial_outpath)
    print('protocol path:', protocol_path)

    workspace = create_workspace(protocol_path)
    program: Program = workspace["drift"]
    oracle_program: Program = workspace["pyth"]
    provider: Provider = program.provider
    from solana.rpc.async_api import AsyncClient
    connection: AsyncClient = provider.connection

    admin_clearing_house, usdc_mint = await setup_bank(program)

    # state modification
    auction_duration = 0
    await admin_clearing_house.update_perp_auction_duration(auction_duration)
    await admin_clearing_house.update_lp_cooldown_time(0)    

    if oracle_guard_rails is not None:
        await admin_clearing_house.update_oracle_guard_rails(oracle_guard_rails)

    # setup the markets
    init_leverage = 0.0002 # set to None if you dont want this 
    perp_market_init_leverage = 5 

    n_markets = len(markets) 
    n_spot_markets = len(spot_markets) + 1
    last_oracle_prices = []
    last_spot_oracle_prices = [1,]
    oracle_addrs = []

    spot_mints = [
        usdc_mint
    ]
    for i, spot_market in enumerate(spot_markets):
        spot_mint, price, oracle = await setup_spot_market(
            admin_clearing_house, 
            oracle_program, 
            spot_market, 
            i+1
        )
        spot_mints.append(spot_mint)
        last_spot_oracle_prices.append(price)
        oracle_addrs.append(oracle)

    for i in range(n_spot_markets):
        await admin_clearing_house.update_update_insurance_fund_unstaking_period(i, 0)
        await admin_clearing_house.update_withdraw_guard_threshold(i, 2**64 - 1)

    for i, market in enumerate(markets):
        oracle_price, oracle = await setup_market(
            admin_clearing_house, 
            oracle_program, 
            market, 
            i,
            perp_market_init_leverage, 
            spread
        )
        last_oracle_prices.append(oracle_price)
        oracle_addrs.append(oracle)

        # allow IF to pay bankruptcies
        await admin_clearing_house.update_perp_market_contract_tier(
            i, 
            ContractTier.A()
        )
        await admin_clearing_house.update_perp_market_max_imbalances(
            i, 
            4000 * QUOTE_PRECISION, 
            100_000_000 * QUOTE_PRECISION, 
            100_000_000 * QUOTE_PRECISION
        )

    # save initial state
    await save_state_account(program, state_path)

    start = time.time()

    # initialize users + deposits
    users = await airdrop_sol_users(provider, events, user_path)
    user_chs, _user_chus, _init_total_collateral = await setup_deposits(events, program, spot_mints, spot_markets, users)

    # compute init collateral 
    async def get_token_amount(usdc_ata: PublicKey, price: int):
        return (await provider.connection.get_token_account_balance(usdc_ata))['result']['value']['uiAmount'] * price
    async def get_collateral_amount(chu: ClearingHouseUser):
        return (await chu.get_total_collateral()) / QUOTE_PRECISION
    async def compute_collateral_amount():
        promises = []
        ch: ClearingHouse
        for (user_idx, ch) in user_chs.items():
            chu: ClearingHouseUser = _user_chus[user_idx]
            # get it all in $ amounts
            user_collateral = get_collateral_amount(chu)
            promises.append(user_collateral)

            for i in ch.spot_market_atas.keys(): 
                if i == 0:
                    price = 1
                else:
                    spot = await get_spot_market_account(program, i)
                    price = (await get_feed_data(oracle_program, spot.oracle)).price

                promises.append(
                    get_token_amount(ch.spot_market_atas[i], price)
                )

        all_user_collateral = await asyncio.gather(*promises)
        all_user_collateral = sum(all_user_collateral)

        return all_user_collateral

    init_total_collateral = await compute_collateral_amount()
    print(f'> initial collateral: {init_total_collateral}')
    assert int(init_total_collateral) == int(_init_total_collateral/QUOTE_PRECISION), f"{init_total_collateral} {_init_total_collateral/QUOTE_PRECISION}"

    global LOGGER
    LOGGER = Logger(f'{trial_outpath}/ix_logs.csv')

    last_event = DepositCollateralEvent

    # process events 
    for i in tqdm(range(len(events))):
        sys.stdout.flush()
        event = events.iloc[i]
        ix_args = None
        ch = None

        ix: TransactionInstruction
        if event.event_name == DepositCollateralEvent._event_name:
            continue

        elif event.event_name == MidSimDepositEvent._event_name:
            event = Event.deserialize_from_row(MidSimDepositEvent, event)
            assert event.user_index in user_chs, 'user doesnt exist'
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch, admin_clearing_house, spot_mints)
            ix_args = event.serialize_parameters()
            print(f'=> {event.user_index} depositing...')

        elif event.event_name == OpenPositionEvent._event_name: 
            event = Event.deserialize_from_row(OpenPositionEvent, event)
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch, init_leverage, oracle_program, adjust_oracle_pre_trade=False)
            if ix is None: continue
            ix_args = place_and_take_ix_args(ix[1])
            print(f'=> {event.user_index} opening position...')

        elif event.event_name == ClosePositionEvent._event_name: 
            event = Event.deserialize_from_row(ClosePositionEvent, event)
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch, oracle_program, adjust_oracle_pre_trade=True)
            if ix is None: continue
            ix_args = place_and_take_ix_args(ix[1])
            print(f'=> {event.user_index} closing position...')

        elif event.event_name == addLiquidityEvent._event_name: 
            event = Event.deserialize_from_row(addLiquidityEvent, event)
            print(f'=> {event.user_index} adding liquidity: {event.token_amount}...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            ix_args = event.serialize_parameters()
            
        elif event.event_name == removeLiquidityEvent._event_name:
            event = Event.deserialize_from_row(removeLiquidityEvent, event)
            assert event.user_index in user_chs, 'user doesnt exist'
            event.lp_token_amount = -1

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            if ix is None: continue
            ix_args = event.serialize_parameters()
            print(f'=> {event.user_index} removing liquidity...')

        elif event.event_name == SettlePnLEvent._event_name:
            event = Event.deserialize_from_row(SettlePnLEvent, event)
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            if ix is None: continue
            print(f'=> {event.user_index} settle pnl...')
            ix_args = event.serialize_parameters()

        elif event.event_name == SettleLPEvent._event_name: 
            event = Event.deserialize_from_row(SettleLPEvent, event)
            print(f'=> {event.user_index} settle lp...')
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            ix_args = event.serialize_parameters()
        
        elif event.event_name == PerpOracleUpdateEvent._event_name: 
            event = Event.deserialize_from_row(PerpOracleUpdateEvent, event)
            event.slot = (await provider.connection.get_slot())['result']
            print(f'=> adjusting oracle: {colored(event.price, "red")}')
            ix = await event.run_sdk(program, oracle_program)
            ix_args = event.serialize_parameters()
            ch = admin_clearing_house

        elif event.event_name == SpotOracleUpdateEvent._event_name: 
            event = Event.deserialize_from_row(SpotOracleUpdateEvent, event)
            event.slot = (await provider.connection.get_slot())['result']
            print(f'=> adjusting spot oracle: {colored(event.price, "red")}')
            ix = await event.run_sdk(program, oracle_program)
            ix_args = event.serialize_parameters()
            ch = admin_clearing_house

            last_spot_oracle_prices[event.market_index] = event.price

        elif event.event_name == LiquidateEvent._event_name:
            # continue
            if last_event._event_name == LiquidateEvent._event_name: 
                continue

            event = Event.deserialize_from_row(LiquidateEvent, event)
            liquidator = Liquidator(user_chs, n_markets, n_spot_markets, event.user_index, send_ix)
            await liquidator.liquidate_loop()
            continue

        elif event.event_name == InitIfStakeEvent._event_name:
            event = Event.deserialize_from_row(InitIfStakeEvent, event)
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            ix_args = event.serialize_parameters()

        elif event.event_name == AddIfStakeEvent._event_name:
            event = Event.deserialize_from_row(AddIfStakeEvent, event)
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            ix_args = event.serialize_parameters()
        
        elif event.event_name == RemoveIfStakeEvent._event_name:
            event = Event.deserialize_from_row(RemoveIfStakeEvent, event)
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            if ix is None: continue
            ix_args = event.serialize_parameters()

        elif event.event_name == WithdrawEvent._event_name:
            event = Event.deserialize_from_row(WithdrawEvent, event)
            ch: SDKClearingHouse = user_chs[event.user_index]
            
            # make sure the oracle isnt stale across all markets they're in 
            for oracle in oracle_addrs:
                last_oracle_price = (await get_feed_data(oracle_program, oracle)).price
                slot = (await provider.connection.get_slot())['result']
                await set_price_feed_detailed(oracle_program, oracle, last_oracle_price, 0, slot)

            ix = await event.run_sdk(ch)
            ix_args = event.serialize_parameters()

        elif event.event_name == UpdateKEvent._event_name:
            event = Event.deserialize_from_row(UpdateKEvent, event) 
            ix = await event.run_sdk(admin_clearing_house)
            ix_args = event.serialize_parameters()
            ch = admin_clearing_house

        elif event.event_name == RepegEvent._event_name:
            event = Event.deserialize_from_row(RepegEvent, event) 
            ix = await event.run_sdk(admin_clearing_house)
            ix_args = event.serialize_parameters()
            ch = admin_clearing_house

        elif event.event_name == NullEvent._event_name: 
            continue

        else:
            print('event:', event)
            raise NotImplementedError 

        need_to_send_ix = ix_args is not None 
        if need_to_send_ix:
            await send_ix(ch, ix, event._event_name, ix_args)        
            last_event = event

        # print('levearged users:')
        # for i, chu in _user_chus.items():
        #     leverage = await chu.get_leverage()
        #     if leverage != 0:
        #         print(i, leverage/10_000)


    print('delisting market...')
    slot = (await provider.connection.get_slot())['result']
    dtime: int = (await provider.connection.get_block_time(slot))['result']

    # + N seconds
    print('updating perp/spot market expiry...')
    seconds_time = 5
    sigs = []
    for i in range(n_markets):
        sig = await admin_clearing_house.update_perp_market_expiry(i, dtime + seconds_time)
        sigs.append(sig)
        LOGGER.log(slot, 'update_perp_market_expiry', {'market_index': i, 'expiry_time': dtime + seconds_time}, None, -1)

    for i in range(n_spot_markets):
        sig = await admin_clearing_house.update_spot_market_expiry(i, dtime + seconds_time)
        sigs.append(sig)
        LOGGER.log(slot, 'update_spot_market_expiry', {'spot_market_index': i, 'expiry_time': dtime + seconds_time}, None, -1)

    # repay withdraws 
    print('repaying withdraws...')
    async def payback_borrows():
        collateral_change = 0

        for i in range(n_spot_markets):
            success = False
            attempt = 0
            while not success:
                routines = []
                attempt += 1
                success = True
                print(colored(f' =>> repaying spot market debt {i} attempt {attempt}', "blue"))

                for (user_idx, ch) in user_chs.items():
                    position = await ch.get_user_spot_position(i)
                    if position is None: 
                        continue
                    
                    spot_market = await get_spot_market_account(program, i)
                    if str(position.balance_type) == "SpotBalanceType.Borrow()":
                        success = False

                        token_amount = sdk_token_amount(
                            position.scaled_balance, 
                            spot_market, 
                            position.balance_type
                        )
                        print(f'{user_idx}: paying back {token_amount}...')

                        current_amount = (await connection.get_token_account_balance(
                            ch.spot_market_atas[i]
                        ))['result']['value']['amount']

                        difference_amount = token_amount - int(current_amount)
                        if difference_amount > 0:
                            # +100 just in case
                            difference_amount = int(difference_amount) + 100 * QUOTE_PRECISION

                            price = (await get_feed_data(oracle_program, spot_market.oracle)).price if i != 0 else 1
                            collateral_change += difference_amount * price / QUOTE_PRECISION

                            print(f'minting an extra {difference_amount}...')
                            mint_tx = _mint_usdc_tx(
                                spot_mints[i], 
                                provider, 
                                difference_amount, 
                                ch.spot_market_atas[i]
                            )
                            await admin_clearing_house.send_ixs(mint_tx.instructions)

                        # pay back 
                        ix = await ch.get_deposit_collateral_ix(
                            int(1e19),
                            i, 
                            ch.spot_market_atas[i],
                            reduce_only=True
                        )
                        ix_args = {'event_name': 'deposit', 'amount': int(1e19), 'reduce_only': True }
                        promise = send_ix(ch, ix, 'deposit_collateral', ix_args)
                        routines.append(promise)

                await asyncio.gather(*routines)
        return collateral_change

    collateral_change = await payback_borrows()
    init_total_collateral += collateral_change

    # close out all the LPs 
    print('closing LPs...')
    routines = []
    routine_chs = []
    for i in range(n_markets):
        for (_, ch) in user_chs.items():
            position = await ch.get_user_position(i)
            if position is None: 
                continue
            if position.lp_shares > 0:
                print(f'removing {position.lp_shares} lp shares...')
                ix = ch.get_remove_liquidity_ix(
                    position.lp_shares, position.market_index
                )
                routines.append(ix)
                routine_chs.append(ch)
    ixs = await asyncio.gather(*routines)

    promises = []
    for ix, ch in zip(ixs, routine_chs):
        ix_args = remove_liquidity_ix_args(ix)
        promises.append(
            send_ix(ch, ix, removeLiquidityEvent._event_name, ix_args)
        )
    await asyncio.gather(*promises)

    print('waiting for expiry...')
    for sig in sigs:
        await provider.connection.confirm_transaction(sig, commitment.Confirmed)
        market = await get_perp_market_account(program, i)
        assert market.expiry_ts != 0, f'{market.expiry_ts} {dtime + seconds_time}'

    while True:
        slot = (await provider.connection.get_slot())['result']
        new_dtime: int = (await provider.connection.get_block_time(slot))['result']
        time.sleep(0.2)
        if new_dtime > dtime + seconds_time: 
            break 

    print('settling expired market')
    for i in range(n_markets):
        await admin_clearing_house.settle_expired_market(i)
        LOGGER.log(slot, 'settle_expired_market', {'market_index': i}, None, -1)

        market = await get_perp_market_account(program, i)
        print(
            f'market {i} expiry_price vs twap/price', 
            market.expiry_price, 
            market.amm.historical_oracle_data.last_oracle_price_twap,
            market.amm.historical_oracle_data.last_oracle_price
        )

    # liquidate em + resolve bankrupts
    await liquidator.liquidate_loop()

    # settle expired positions 
    print('settling expired positions...')
    for i in range(n_markets):
        number_positions = 0
        for (_, ch) in user_chs.items():
            position = await ch.get_user_position(i)
            if position is None: continue
            number_positions += 1
        print(f'market {i}: number of positions:', number_positions)

        market = await get_perp_market_account(program, i)
        print(
            f'market {i} net long/short',
            market.amm.base_asset_amount_long, 
            market.amm.base_asset_amount_short, 
            market.number_of_users, 
        )

    # remove if stakes 
    for i in range(n_spot_markets):
        for (user_index, ch) in user_chs.items():
            if_position_pk = get_insurance_fund_stake_public_key(
                ch.program_id, ch.authority, i
            )
            resp = await ch.program.provider.connection.get_account_info(
                if_position_pk
            )
            if resp["result"]["value"] is None: continue # if stake doesnt exist 

            if_account = await get_if_stake_account(ch.program, ch.authority, i)
            if if_account.if_shares > 0:
                event = RemoveIfStakeEvent(-1, user_index, i, -1)
                ix = await event.run_sdk(ch)
                if ix is None: continue
                ix_args = event.serialize_parameters()

                await send_ix(ch, ix, event._event_name, ix_args)        

    n_users = len(list(user_chs.keys()))
    for i in range(n_markets):
        success = False
        attempt = -1

        market = await get_perp_market_account(program, i)
        last_oracle_price = (await get_feed_data(oracle_program, market.amm.oracle)).price

        while not success:
            attempt += 1
            success = True
            user_count = 0

            print(colored(f' =>> market {i}: settle attempt {attempt}', "blue"))
            for (user_index, ch) in user_chs.items():
                position = await ch.get_user_position(i)

                # dont let oracle go stale
                slot = (await provider.connection.get_slot())['result']
                await set_price_feed_detailed(oracle_program, market.amm.oracle, last_oracle_price, 0, slot)

                # settle expired position
                if position is None: 
                    user_count += 1
                    print(colored(f'settled expired position success: {user_count}/{n_users}', 'green'))
                else:
                    ix = await ch.get_settle_pnl_ix(ch.authority, i)
                    ix_args = settle_pnl_ix_args(ix[1])

                    failed = await send_ix(ch, ix, SettlePnLEvent._event_name, ix_args, silent_success=True)
                    if not failed:
                        user_count += 1
                        print(colored(f'settled expired position success: {user_count}/{n_users}', 'green'))
                    else: 
                        settling_position = await ch.get_user_position(i)
                        scaled_balance = (await ch.get_user()).spot_positions[0].scaled_balance
                        print('user', i, str(ch.authority), ': ', '$',scaled_balance/SPOT_BALANCE_PRECISION)
                        print('settling position:', settling_position)

                        print(colored(f'settled expired position failed: {user_count}/{n_users}', 'red'))
                        success = False

    # some positions go into borrow after expired position is at a loss
    collateral_change = await payback_borrows()
    init_total_collateral += collateral_change

    for spot_market_index in range(n_spot_markets):
        success = False
        attempt = -1
        spot_market = await get_spot_market_account(program, spot_market_index)
        if spot_market_index != 0:
            last_oracle_price = (await get_feed_data(oracle_program, spot_market.oracle)).price

        while not success:
            attempt += 1
            success = True
            user_withdraw_count = 0

            print(colored(f' =>> market {spot_market_index}: withdraw attempt {attempt}', "blue"))
            for (i, ch) in user_chs.items():
                chu: ClearingHouseUser = _user_chus[i]

                # dont let oracle go stale
                if spot_market_index != 0:
                    slot = (await provider.connection.get_slot())['result']
                    await set_price_feed_detailed(oracle_program, spot_market.oracle, last_oracle_price, 0, slot)

                position = await chu.get_user_spot_position(spot_market_index)
                if position is None: 
                    user_withdraw_count += 1
                    continue

                # # balance: int, spot_market: SpotMarket, balance_type: SpotBalanceType
                spot_market = await get_spot_market_account(program, spot_market_index)
                token_amount = int(sdk_token_amount(
                    position.scaled_balance, 
                    spot_market,
                    position.balance_type
                ))

                # withdraw all of collateral
                print('token amount', token_amount)

                ix = await ch.get_withdraw_collateral_ix(
                    # token_amount, 
                    int(1e19),
                    spot_market_index, 
                    ch.spot_market_atas[spot_market_index],
                    True
                )
                ix_args = withdraw_ix_args(ix)
                failed = await send_ix(ch, ix, WithdrawEvent._event_name, ix_args)

                if not failed:
                    user_withdraw_count += 1
                    print(colored(f'withdraw success: {user_withdraw_count}/{n_users}', 'green'))
                    spot_position = await ch.get_user_spot_position(spot_market_index)
                    if spot_position is not None: 
                        print(spot_position)
                        success = False
                else: 
                    print(colored(f'withdraw failed: {user_withdraw_count}/{n_users}', 'red'))
                    success = False

    for (_, ch) in user_chs.items():
        for i in range(n_markets):
            position = await ch.get_user_position(i)
            if position is None: continue
            print(position)
        
        for i in range(n_spot_markets):
            position = await ch.get_user_spot_position(i)
            if position is None: continue
            print(position)

    # skip for now
    # await admin_clearing_house.settle_expired_market_pools_to_revenue_pool(0)

    for i in range(n_markets):
        market = await get_perp_market_account(program, i)
        print('=> market', i, market.status)

    # df = pd.DataFrame(df_rows)
    # df.to_csv('tmp.csv', index=False)

    # # close out anyone who hasnt already closed out 
    # print('closing out everyone...')
    # net_baa = 1 
    # market = await get_perp_market_account(program, 0)
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
    end_total_collateral = await compute_collateral_amount()

    total_market_money = 0
    for i in range(n_markets):
        market = await get_perp_market_account(program, i)
        market_collateral = market.amm.total_fee_minus_distributions / 1e6
        end_total_collateral += market_collateral

        total_market_money += market.amm.fee_pool.scaled_balance + market.pnl_pool.scaled_balance

        print(
            f'market {i} info:',
            "\n\t market.amm.total_fee_minus_distributions:", 
            market.amm.total_fee_minus_distributions,
            "\n\t net baa & net unsettled:", 
            market.amm.base_asset_amount_with_amm,
            market.amm.base_asset_amount_with_unsettled_lp,
            market.amm.base_asset_amount_with_amm + market.amm.base_asset_amount_with_unsettled_lp,
            '\n\t net long/short',
            market.amm.base_asset_amount_long, 
            market.amm.base_asset_amount_short, 
            market.amm.user_lp_shares, 
            '\n\t cumulative_social_loss / funding:',
            market.amm.total_social_loss, 
            market.amm.cumulative_funding_rate_long, 
            market.amm.cumulative_funding_rate_short, 
            market.amm.last_funding_rate_long, 
            market.amm.last_funding_rate_short, 
            '\n\t fee pool:', market.amm.fee_pool.scaled_balance, 
            '\n\t pnl pool:', market.pnl_pool.scaled_balance
        )
    print('---')

    for i in range(n_spot_markets):
        spot_market = await get_spot_market_account(program, i)

        print(
            f'spot market {i} info:', '\n\t',
            'deposit_balance:', spot_market.deposit_balance, '\n\t',
            'borrow_balance:', spot_market.borrow_balance, '\n\t',
            'revenue_pool:', spot_market.revenue_pool.scaled_balance,'\n\t',
            'spot_fee_pool:', spot_market.spot_fee_pool.scaled_balance,'\n\t',
            'total if shares', spot_market.insurance_fund.total_shares,
        )
        if i == 0:
            total_balance = spot_market.revenue_pool.scaled_balance + total_market_money
            print(f'total balance (should == deposit balance? {total_balance == spot_market.deposit_balance}):', total_balance)

    print('---')

    print(f'collateral information:')
    print(f'\tcollateral before: {end_total_collateral} \n\t collateral after: {end_total_collateral}')
    print(f'\tdifference in collateral: {(end_total_collateral - init_total_collateral) / QUOTE_PRECISION:,}')

    print(
        'total sim time (seconds):',
        time.time() - start
    )
    
    await provider.close()
    await close_workspace(workspace)


async def main(protocol_path, experiments_folder, geyser_path, trial):
    events = pd.read_csv(f"{experiments_folder}/events.csv")

    no_oracle_guard_rails = OracleGuardRails(
        price_divergence=PriceDivergenceGuardRails(1, 1), 
        validity=ValidityGuardRails(10, 10, 100, 2**63 - 1)
    )

    trial_guard_rails = None
    spread = None

    if 'spread_250' in trial:
        print('=> spread 250 activated')
        spread = 250
        trial_guard_rails = no_oracle_guard_rails
   
    if 'spread_1000' in trial:
        print('=> spread 1000 activated')
        spread = 1000
        trial_guard_rails = no_oracle_guard_rails

    if 'no_oracle_guards' in trial:
        print('=> no_oracle_guard_rails activated')
        trial_guard_rails = no_oracle_guard_rails

    # read and load initial clearing house state (thats all we use chs.csv for...)
    with open(f'{experiments_folder}/markets_json.csv', 'r') as f:
        markets = json.load(f)
    with open(f'{experiments_folder}/spot_markets_json.csv', 'r') as f:
        spot_markets = json.load(f)

    if len(spot_markets) > 5:
        print('WARNING: ONLY UP TO FIVE SPOT MARKETS SUPPORTED (check db_path/update_config.py)')

    experiment_name = Path(experiments_folder).stem
    trial_outpath = Path(f'{experiments_folder}/../../results/{experiment_name}/trial_{trial}')
    trial_outpath.mkdir(exist_ok=True, parents=True)
    state_path = f'{trial_outpath}/init_state.json' 
    user_path = f'{trial_outpath}/users.json'

    setup_run_info(str(trial_outpath), protocol_path, '')

    val = LocalValidator(protocol_path, geyser_path)
    val.start()
    try:
        await run_trial(
            protocol_path, 
            events, 
            markets, 
            spot_markets,
            trial_outpath, 
            state_path,
            user_path,
            trial_guard_rails, 
            spread
        )
    finally:
        val.stop()

        # save logs
        global LOGGER
        LOGGER.export()

        # export state over time with geyser to trail_outpath
        # run script with -- output path flags etc.
        import extract
        extract.main(
            protocol_path, 
            trial_outpath, 
            user_path, 
            state_path,
        )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=str, required=True)
    parser.add_argument('--protocol', type=str, required=False, default='../driftpy/protocol-v2')
    parser.add_argument('--geyser', type=str, required=False, default='../solana-accountsdb-plugin-postgres')
    parser.add_argument('--ignore-compute', action='store_true')

    # trials = ['no_oracle_guards', 'spread_250', 'spread_1000', 'oracle_guards',]
    parser.add_argument('-t', '--trial', type=str, required=False, default='')

    global args
    args = parser.parse_args()

    if args.ignore_compute:
        print('=> ignoring compute used in ixs')

    try: 
        import asyncio
        asyncio.run(main(args.protocol, args.events, args.geyser, args.trial))
    finally:
        pass

