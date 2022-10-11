#%%
import sys
from typing import final

from tqdm.utils import ObjectWrapper

from driftpy import admin
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

from driftpy.setup.helpers import _create_usdc_mint, mock_oracle, _airdrop_user, set_price_feed, set_price_feed_detailed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_usdc_ata_tx
from driftpy.clearing_house import ClearingHouse
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account
from driftpy.math.amm import calculate_mark_price_amm

from anchorpy import Provider, Program, create_workspace, close_workspace
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


async def save_state(program, experiments_folder, event_i, user_chs):


    def human_amm_df(amm: AMM):
        bool_fields = [ 'last_oracle_valid']
        enum_fields = ['oracle_source']
        pure_fields = ['last_update_slot', 'long_intensity_count', 'short_intensity_count', 
        'curve_update_intensity', 'amm_jit_intensity'
        ]
        reserve_fields = [
            'base_asset_reserve', 'quote_asset_reserve', 'min_base_asset_reserve', 'max_base_asset_reserve', 'sqrt_k'
            'ask_base_asset_reserve', 'ask_quote_asset_reserve', 'bid_base_asset_reserve', 'bid_quote_asset_reserve'
            'terminal_quote_asset_reserve', 'base_asset_amount_long', 'base_asset_amount_short', 'base_asset_amount_with_amm', 'base_asset_amount_with_unsettled_lp',
            'user_lp_shares'
            ]
        pct_fields = ['long_spread', 'short_spread', 'concentration_coef',]
        funding_fields = ['cumulative_funding_rate_long', 'cumulative_funding_rate_short', 'last_funding_rate', 'last_funding_rate_long', 'last_funding_rate_short', 'last24h_avg_funding_rate']
        quote_asset_fields = ['total_fee', 'total_mm_fee', 'total_exchange_fee', 'total_fee_minus_distributions',
        'total_fee_withdrawn', 'total_liquidation_fee', 'cumulative_social_loss', 'net_revenue_since_last_funding',
        'quote_asset_amount_long', 'quote_asset_amount_short', 'quote_entry_amount_long', 'quote_entry_amount_short',
        'volume24h', 'long_intensity_volume', 'short_intensity_volume',]
        time_fields = ['last_mark_price_twap_ts', 'last_oracle_price_twap_ts']
        duration_fields = ['lp_cooldown_time']
        px_fields = ['last_bid_price_twap', 'last_ask_price_twap', 'last_mark_price_twap', 'last_mark_price_twap5min',
        'peg_multiplier',
        'mark_std']
        pool_fields = ['fee_pool']


    def human_market_df(market: PerpMarket):
        enum_fields = ['status', 'contract_tier', '']
        pure_fields = ['number_of_users', 'market_index', 'next_curve_record_id', 'next_fill_record_id', 'next_funding_rate_record_id']
        pct_fields = ['imf_factor', 'unrealized_pnl_imf_factor', 'liquidator_fee', 'if_liquidation_fee',
        'margin_ratio_initial', 'margin_ratio_maintenance']
        px_fields = ['expiry_price', ]
        time_fields = ['last_trade_ts', 'expiry_ts']
        pool_fields = ['pnl_pool']

        dffull = pd.DataFrame(market.__dict__)



    market: PerpMarket = await get_perp_market_account(program, 0)
    print(str(market.status))
    # assert(str(market.status) == str(MarketStatus.Active()))
    d = market.__dict__
    d2 = market.amm.__dict__  
    d3 = market.amm.historical_oracle_data.__dict__
    d.pop('padding')
    d.update(d2)
    d.update(d3)

    # if event_i > 40:
    #     import pdb; pdb.set_trace()
    # print(d)
    df = pd.DataFrame(d, index=list(range(6))).head(1)
    # print(df)
    outfile = f"./{experiments_folder}/result_market0.csv"
    # print('event i going to file:', outfile)
    if event_i > 0:
        df.to_csv(outfile, mode="a", index=False, header=False)
    else:
        df.to_csv(outfile, index=False)


    all_users = await program.account["User"].all()
    for (i, user_ch) in user_chs.items():
        upk = (user_ch.authority)
        user_account: PerpMarket = await get_user_account(program, upk, 0)
        # try:
        uu = user_account.__dict__
        uu.pop('orders')
        uu.pop('name')
        uu.pop('padding')
        # print(pd.DataFrame(uu))
        df = pd.DataFrame(uu, index=list(range(8))).head(1)
        # print(df)
        outfile = f"./{experiments_folder}/result_user_"+str(i)+".csv"
        # print('event i going to file:', outfile)
        if event_i > 0:
            df.to_csv(outfile, mode="a", index=False, header=False)
        else:
            df.to_csv(outfile, index=False)
            # except Exception as e:
            #     print(e)
            #     pass



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


async def run_trial(protocol_path, events, clearing_houses, trial_outpath, oracle_guard_rails=None, spread=None):
    print('trial_outpath:', trial_outpath)
    os.makedirs(trial_outpath, exist_ok=True)

    df_row_index = 0
    print('creating workspace: %s' % protocol_path)
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
    await admin_clearing_house.initialize_perp_market(
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
    if oracle_guard_rails is not None:
        await admin_clearing_house.update_oracle_guard_rails(oracle_guard_rails)

    if spread is not None:
        await admin_clearing_house.update_perp_market_curve_update_intensity(0, 100)
        await admin_clearing_house.update_perp_market_base_spread(0, spread)

    # await admin_clearing_house.
    await admin_clearing_house.update_perp_auction_duration(0)
    await admin_clearing_house.update_lp_cooldown_time(0, 0)
    await admin_clearing_house.update_perp_market_max_fill_reserve_fraction(0, 1)
    await admin_clearing_house.update_perp_market_step_size_and_tick_size(0, int(AMM_RESERVE_PRECISION/1e4), 1)


    initial_state: State = await get_state_account(program)
    initial_state_d = initial_state.__dict__

    for x in ['admin', 'whitelist_mint', 'discount_mint', 'signer', 'srm_vault', 'exchange_status']:
        initial_state_d[x] = str(initial_state_d[x])

    class ComplexEncoder(json.JSONEncoder):
         def default(self, obj):
            if isinstance(obj, object):
                 return obj.__dict__
             # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)

    for x in ['oracle_guard_rails', 'spot_fee_structure', 'perp_fee_structure']:
        initial_state_d[x] = initial_state_d[x].__dict__

    state_outfile = f"{trial_outpath}/init_state.json"
    with open(state_outfile, "w") as outfile:
        json_string = json.dumps(initial_state_d,
            sort_keys=True, 
            cls=ComplexEncoder,
            skipkeys=True,
            indent=4)
        json.dump(json_string, outfile)

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

    deposit_amounts[liquidator_index] = 10_000_000 * QUOTE_PRECISION

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

            if position and position.base_asset_amount == 0 and position.quote_asset_amount < 0:
                promise = liquidator_clearing_house.liquidate_perp_pnl_for_deposit(
                    authority,
                    0,
                    0,
                    abs(position.quote_asset_amount) # take it fully on
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

        # try:
        await derisk()
        await resolve_bankruptcies()
        # except: 
        #     print('derisk / bankrupt error (TODO)')
        #     pass

    async def resolve_bankruptcies():
        ch: ClearingHouse
        user_promises = []
        did_resolve = False
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
            if user.is_bankrupt:
                promise = liquidator_clearing_house.resolve_perp_bankruptcy(
                    user.authority,  0
                )
                promises.append(promise)

        for promise in promises:
            await promise
            from termcolor import colored
            print(colored('     *** bankrupt resolved ***   ', "green"))
            did_resolve = True
        return did_resolve
        
    async def derisk():
        ch = liquidator_clearing_house
        position = await ch.get_user_position(0)
        if position is None or position.base_asset_amount == 0: 
            return

        market = await get_perp_market_account(ch.program, 0)
        slot = (await provider.connection.get_slot())['result']
        time: int = (await provider.connection.get_block_time(slot))['result']

        print(f'=> liquidator derisking {position.base_asset_amount} baa in market status:', market.status)
        if str(market.status) == "MarketStatus.Settlement()" or market.expiry_ts  >= time:
            try:
                print(f'=> liquidator settling expired position')
                await ch.settle_pnl(liquidator_clearing_house.authority, 0)
            except:
                pass
        else:
            await ch.close_position(0)

    # todo 
    #   calculate margin requirements of user same as js sdk 

    df_rows = {}
    for i in tqdm(range(len(events))):
        event = events.iloc[i]

        if event.event_name == DepositCollateralEvent._event_name:
            pass

        elif event.event_name == OpenPositionEvent._event_name: 
            event = Event.deserialize_from_row(OpenPositionEvent, event)
            print(f'=> {event.user_index} opening position...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            sig = await event.run_sdk(ch, init_leverage, oracle_program, adjust_oracle_pre_trade=False)

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
            event.slot = (await provider.connection.get_slot())['result']
            print(f'=> adjusting oracle: {event.price}')
            await event.run_sdk(program, oracle_program)

        elif event.event_name == 'liquidate':
            print('=> liquidating...')
            await try_liquidate()
        
        elif event.event_name == NullEvent._event_name: 
            continue
        
        #
        await try_liquidate()
        await try_liquidate()

        # track market state after event
        await save_state(program, trial_outpath, i, user_chs)
        df_row_index += 1

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
    await admin_clearing_house.update_perp_market_expiry(0, time + seconds_time)
    
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
    await admin_clearing_house.settle_expired_market(0)
    await save_state(program, trial_outpath, df_row_index, user_chs)
    df_row_index+=1

    market = await get_perp_market_account(
        program, 0
    )
    print(
        'market expiry_price vs twap/price', 
        market.expiry_price, 
        market.amm.historical_oracle_data.last_oracle_price_twap,
        market.amm.historical_oracle_data.last_oracle_price
    )


    # liquidate em + resolve bankrupts
    await try_liquidate()
    await try_liquidate()

    # cancel open orders
    routines = []
    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is not None and position.open_orders > 0:
            routines.append(
                ch.cancel_order()
            )

    await save_state(program, trial_outpath, df_row_index, user_chs)
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

    market = await get_perp_market_account(program, 0)
    print(
        'net long/short',
        market.amm.base_asset_amount_long, 
        market.amm.base_asset_amount_short, 
        market.number_of_users, 
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
                settling_position = await ch.get_user_position(0)
                scaled_balance = (await ch.get_user()).spot_positions[0].scaled_balance
                print('user', i, str(ch.authority), ': ', '$',scaled_balance/SPOT_BALANCE_PRECISION)
                print('settling position:', settling_position)
                await ch.settle_pnl(ch.authority, 0)
                user_count += 1
                print(colored(f'     *** settle expired position successful {user_count}/{n_users} ***   ', "green"))
                await save_state(program, trial_outpath, df_row_index, user_chs)
                df_row_index+=1
            except Exception as e:
                if "0x17e2" in e.args[0]['message']: # pool doesnt have enough 
                    print(colored(f'     *** settle expired position failed... ***   ', "red"))
                    print(e.args)
                    success = False
                elif "0x17C0" in e.args[0]['message']: # pool doesnt have enough 
                    print(colored(f'     *** settle expired position failed InsufficientCollateralForSettlingPNL... ***   ', "red"))
                    print(e.args)
                    success = False
                else: 
                    raise Exception(e)

            market = await get_perp_market_account(program, 0)
            print(
                'net long/short',
                market.amm.base_asset_amount_long, 
                market.amm.base_asset_amount_short, 
                market.number_of_users, 
            )

    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is None: 
            continue
        print(position)

    # skip for now
    # await admin_clearing_house.settle_expired_market_pools_to_revenue_pool(0)

    market = await get_perp_market_account(
        program, 0
    )
    print(market.status)

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
    end_total_collateral = 0 
    for (i, ch) in user_chs.items():
        user = await get_user_account(
            program, 
            ch.authority, 
        )
        balance = user.spot_positions[0].scaled_balance / SPOT_BALANCE_PRECISION * QUOTE_PRECISION
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

    usdc_spot_market = await get_spot_market_account(program, 0)

    print(
        'usdc spot market info:',
        'deposit_balance:', usdc_spot_market.deposit_balance, 
        'borrow_balance:', usdc_spot_market.borrow_balance, 
        'revenue_pool:', usdc_spot_market.revenue_pool.scaled_balance,
        'spot_fee_pool:', usdc_spot_market.spot_fee_pool.scaled_balance,
    )


    market = await get_perp_market_account(program, 0)
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
        market.amm.base_asset_amount_with_amm, 
        market.amm.base_asset_amount_with_unsettled_lp,
        market.amm.base_asset_amount_with_amm + market.amm.base_asset_amount_with_unsettled_lp
    )

    print(
        'net long/short',
        market.amm.base_asset_amount_long, 
        market.amm.base_asset_amount_short, 
        market.amm.user_lp_shares, 
    )

    print(
        'cumulative_social_loss / funding:',
        market.amm.cumulative_social_loss, 
        market.amm.cumulative_funding_rate_long, 
        market.amm.cumulative_funding_rate_short, 
        market.amm.last_funding_rate_long, 
        market.amm.last_funding_rate_short, 
    )

    print(
        'market pool balances:: ',
        'fee pool:', market.amm.fee_pool.scaled_balance, 
        'pnl pool:', market.pnl_pool.scaled_balance
    )

    print(
        'total time (seconds):',
        time.time() - start
    )
    
    await provider.close()
    await close_workspace(workspace)


async def main(protocol_path, experiments_folder):
    # e.g.
    # protocol_path = "../driftpy/protocol-v2/"#
    # experiments_folder = 'tmp2'
    events = pd.read_csv(f"./{experiments_folder}/events.csv")
    clearing_houses = pd.read_csv(f"./{experiments_folder}/chs.csv")
    trials = ['no_oracle_guards', 'spread', 'oracle_guards']

    
    for trial in trials:
        no_oracle_guard_rails = OracleGuardRails(
            price_divergence=PriceDivergenceGuardRails(1, 1), 
            validity=ValidityGuardRails(10, 10, 100, 100),
        use_for_liquidations=True)
        
        trial_guard_rails = None
        spread = None

        if 'spread_250' in trial:
            print('spread_250 activated')
            spread = 250

        if 'no_oracle_guards' in trial:
            print('no_oracle_guard_rails activated')
            trial_guard_rails = no_oracle_guard_rails

        val = LocalValidator(protocol_path)
        val.start()
        try:
            print(trial_guard_rails)
            await run_trial(protocol_path, events, clearing_houses, f"./{experiments_folder}/trial_{trial}", trial_guard_rails, spread)
        finally:
            val.stop()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=str, required=True)
    parser.add_argument('--protocol', type=str, required=True)
    args = parser.parse_args()

    try: 
        import asyncio
        asyncio.run(main(args.protocol, args.events))
    finally:
        pass

# %%
