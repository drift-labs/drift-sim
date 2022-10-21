#%%
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

from driftpy.setup.helpers import _create_usdc_mint, mock_oracle, _airdrop_user, set_price_feed, set_price_feed_detailed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_usdc_ata_tx
from driftpy.clearing_house import ClearingHouse
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account
from driftpy.math.amm import calculate_mark_price_amm

from anchorpy import Provider, Program, create_workspace, close_workspace
from sim.driftsim.clearing_house.state.market import SimulationAMM, SimulationMarket
from helpers import setup_run_info, init_user, setup_bank, setup_market, view_logs, save_state
from tqdm import tqdm
from driftpy.setup.helpers import _create_user_usdc_ata_tx
from driftpy.clearing_house_user import ClearingHouseUser
from solana.keypair import Keypair

from typing import Optional, Union, cast, Dict
import json
from pathlib import Path
from solana.publickey import PublicKey
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.idl import Idl, _Metadata
WorkspaceType = Dict[str, Program]

from termcolor import colored
from subprocess import Popen
import os 
import time 
import signal
from solana.transaction import TransactionInstruction
from client.instructions.place_order import layout

class LocalValidator:
    def __init__(self, protocol_path, geyser_path) -> None:
        self.protocol_path = protocol_path
        self.geyser_path = geyser_path
        
    def start(self):
        """
        builds the protocol (from protocol path)
        sets up geyser plugin to get state from (from geyser path)
        starts a new solana-test-validator with a bunch of custom args to 
        launch program + use geyser
        """

        self.log_file = open('node.txt', 'w')

        process = Popen("anchor build".split(' '), cwd=self.protocol_path)
        process.wait()

        process = Popen("bash setup.sh".split(' '), cwd=self.geyser_path)
        process.wait()

        self.proc = Popen(
            f'bash localnet.sh {self.protocol_path} {self.geyser_path}'.split(' '), 
            stdout=self.log_file, 
            preexec_fn=os.setsid, 
        )
        time.sleep(5)

    def stop(self):
        self.log_file.close()
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)  

# copypastad from anchorpy
def create_workspace(
    path: Optional[Union[Path, str]] = None, url: Optional[str] = None
) -> WorkspaceType:
    """loads programs + idls from a specific workspace with a custom wallet path 
    (we need this bc we're loading from a localvalidator and not anchor localnet)
    (we need a custom localvalidator bc we need a geyser plugin to log account changes from the validator)
    """
    result = {}
    project_root = Path.cwd() if path is None else Path(path)
    idl_folder = project_root / "target/idl"
    # keypair_folder = project_root / 'target/deploy/'

    from solana.rpc.async_api import AsyncClient
    from anchorpy.provider import Wallet
    client = AsyncClient()
    
    with open('./anchor.json', 'r') as f: secret = json.load(f) 
    kp = Keypair.from_secret_key(bytes(secret))
    wallet = Wallet(kp)
    provider = Provider(client, wallet)

    for file in idl_folder.iterdir():
        with file.open() as f:
            idl_dict = json.load(f)
        idl = Idl.from_json(idl_dict)

        if file.stem == 'mock_usdc_faucet':
            continue

        with open(project_root/f'programs/{file.stem}/src/lib.rs', 'r') as f:
            data = f.read()
        import re 
        re_result = re.search('\[cfg\(not\(feature = \"mainnet-beta\"\)\)\]\ndeclare_id!\(\"(.*)\"\)', data)
        id = PublicKey(re_result.group(1))
        
        program = Program(idl, id, provider)
        result[idl.name] = program
        
    return result

class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, object):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

async def save_state(program, trial_outpath):
    """dumps state struct to a json to trial_outpath/init_state.json
    """
    initial_state: State = await get_state_account(program)
    initial_state_d = initial_state.__dict__

    for x in ['admin', 'whitelist_mint', 'discount_mint', 'signer', 'srm_vault', 'exchange_status']:
        initial_state_d[x] = str(initial_state_d[x])

    for x in ['oracle_guard_rails', 'spot_fee_structure', 'perp_fee_structure']:
        initial_state_d[x] = initial_state_d[x].__dict__

    state_outfile = f"{trial_outpath}/init_state.json"
    with open(state_outfile, "w") as outfile:
        json.dump(
            initial_state_d, 
            outfile, 
            sort_keys=True, 
            cls=ObjectEncoder,
            skipkeys=True,
            indent=4
        )

async def airdrop_sol_users(provider, events, trial_outpath):
    """airdrops sol to all users in a sim and saves their kps to the outpath 

    Args:
        provider (Provider): 
        events (): sim events
        trial_outpath (str): where to save user keypairs

    Returns:
        (list of user keypairs, liquidator's index)
    """

    print('=> airdropping sol to users...')
    user_indexs = np.unique([json.loads(e['parameters'])['user_index'] for _, e in events.iterrows() if 'user_index' in json.loads(e['parameters'])])
    user_indexs = list(np.sort(user_indexs))

    liquidator_index = len(user_indexs)
    user_indexs.append(liquidator_index) # liquidator

    users = {}
    for user_index in tqdm(user_indexs):
        user, tx_sig = await _airdrop_user(provider)
        users[user_index] = (user, tx_sig)

    # save user pks for later 
    json_users = {}
    kp: Keypair
    for u, (kp, _) in users.items():
        json_users[str(u)] = str(kp.public_key)
    with open(f'{trial_outpath}/users.json', 'w') as f:
        json.dump(json_users, f)

    for user, tx_sig in tqdm(users.values()):
        await provider.connection.confirm_transaction(tx_sig, sleep_seconds=0.1)
    
    return users, liquidator_index

class Liquidator: 
    def __init__(self, user_chs, n_markets, liquidator_index) -> None:
        """class for a liquidator 

        Args:
            user_chs (dict(user_index => clearing_house)): all users we want to try to liq
            n_markets (int): number of markets to try to liq from 
            liquidator_index (int): user_chs[liquidator_index] == liquidator's clearing house 

        note we dont try to liquidate the liquidator (bc you cant liq yourself)
        """
        self.user_chs = user_chs
        self.n_markets = n_markets
        self.liq_ch: ClearingHouse = user_chs[liquidator_index]

    async def liquidate_loop(self):
        await self.try_liquidate_perp()
        await self.try_liquidate_pnl()
        await self.resolve_bankruptcies()
        await self.derisk()

    async def try_liquidate_perp(self):
        ch: ClearingHouse
        promises = []

        for ch in self.user_chs.values(): 
            for i in range(self.n_markets):
                authority = ch.authority
                if authority == self.liq_ch.authority: 
                    continue
                position = await ch.get_user_position(i)

                if position and position.base_asset_amount != 0:
                    promise = self.liq_ch.liquidate_perp(
                        authority, 
                        i,
                        abs(position.base_asset_amount) # take it fully on
                    )
                    promises.append(promise)

                if position and position.base_asset_amount == 0 and position.quote_asset_amount < 0:
                    promise = self.liq_ch.liquidate_perp_pnl_for_deposit(
                        authority,
                        i,
                        0,
                        abs(position.quote_asset_amount) # take it fully on
                    )
                    promises.append(promise)

        for promise in promises:
            try:
                sig = await promise
                # await view_logs(sig, provider)
                print(colored('     *** liquidation successful ***   ', "green"))
            except Exception as e:
                if "0x1774" in e.args[0]['message']: # sufficient collateral
                    continue 
                # elif "0x1793" in e.args[0]['message']: # invalid oracle
                #     continue 
                # else: 
                #     raise Exception(e)

                print(colored('     *** liquidation failed ***   ', "red"))
                print(e.args)

    async def try_liquidate_pnl(self):
        promises = []
        for ch in self.user_chs.values(): 
            for i in range(self.n_markets):
                authority = ch.authority
                if authority == self.liq_ch.authority: 
                    continue
                position = await ch.get_user_position(i)

                if position and position.base_asset_amount == 0 and position.quote_asset_amount < 0:
                    promise = self.liq_ch.liquidate_perp_pnl_for_deposit(
                        authority,
                        i,
                        0,
                        abs(position.quote_asset_amount) # take it fully on
                    )
                    promises.append(promise)

        for promise in promises:
            try:
                sig = await promise
                # await view_logs(sig, provider)
                print(colored('     *** liquidation successful ***   ', "green"))
            except Exception as e:
                if "0x1774" in e.args[0]['message']: # sufficient collateral
                    continue 
                # elif "0x1793" in e.args[0]['message']: # invalid oracle
                #     continue 
                # else: 
                #     raise Exception(e)

                print(colored('     *** liquidation failed ***   ', "red"))
                print(e.args)

    async def resolve_bankruptcies(self):
        ch: ClearingHouse
        user_promises = []
        chs = []
        for ch in self.user_chs.values(): 
            authority = ch.authority
            if authority == self.liq_ch.authority: 
                continue
            user = ch.get_user()
            user_promises.append(user)
            chs.append(ch)
        users = await asyncio.gather(*user_promises)

        promises = []
        user: User
        for ch, user in zip(chs, users):
            if user.is_bankrupt:
                for i in range(self.n_markets):
                    position = await ch.get_user_position(i)
                    if not is_available(position):
                        promise = self.liq_ch.resolve_perp_bankruptcy(
                            user.authority, i
                        )
                        promises.append(promise)

        did_resolve = False
        for promise in promises:
            await promise
            print(colored('     *** bankrupt resolved ***   ', "green"))
            did_resolve = True

        return did_resolve
        
    async def derisk(self):
        ch = self.liq_ch
        position = await ch.get_user_position(0)
        if position is None or position.base_asset_amount == 0: 
            return

        provider = self.liq_ch.program.provider
        slot = (await provider.connection.get_slot())['result']
        liq_time = (await provider.connection.get_block_time(slot))['result']
        print(f'=> liquidator derisking {position.base_asset_amount} baa in market status:', market.status)

        for i in range(self.n_markets):
            market = await get_perp_market_account(ch.program, i)

            if str(market.status) == "MarketStatus.Settlement()" or market.expiry_ts >= liq_time:
                try:
                    print(f'=> liquidator settling expired position')
                    await ch.settle_pnl(self.liq_ch.authority, i)
                except:
                    pass
            else:
                try:
                    await ch.close_position(i)
                except:
                    pass

async def setup_usdc_deposits(
    events, 
    program, 
    usdc_mint, 
    users, 
    liquidator_index
):
    user_chs = {}
    user_chus = {}
    init_total_collateral = 0 

    # deposit all at once for speed 
    deposit_amounts = {}
    for i in tqdm(range(len(events))):
        event = events.iloc[i]
        if event.event_name == DepositCollateralEvent._event_name:
            event = Event.deserialize_from_row(DepositCollateralEvent, event)
            deposit_amounts[event.user_index] = deposit_amounts.get(event.user_index, 0) + event.deposit_amount

    # dont let the liquidator get liq'd 
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
            deposit_amount, 
            user_kp
        )
        routines.append(routine)

        # track collateral 
        init_total_collateral += deposit_amount

    await asyncio.gather(*routines)

    return user_chs, user_chus, init_total_collateral

def parse_ix_args(ix, layout, identifier):
    """ix => ix_args dictionary using anchorpy's layout
    """
    data = ix.data
    args = layout.parse(data.split(identifier)[1])
    dargs = dict(args)
    dargs.pop('_io')
    return dargs

async def setup_market(
    admin_clearing_house: ClearingHouse, 
    oracle_program: Program, 
    market: dict, 
    market_index: int,
    init_leverage: int, 
    oracle_guard_rails, 
    spread
):
    i = market_index
    init_reserves = int(int(market['base_asset_reserve']) / 1e13 * AMM_RESERVE_PRECISION)
    peg = market['peg_multiplier']
    oracle_price = peg / PEG_PRECISION

    print(f"=> initializing market {i}...")
    print('\t> initial reserves:', init_reserves / AMM_RESERVE_PRECISION)
    print('\t> init peg (init oracle price too):', oracle_price)

    oracle = await mock_oracle(oracle_program, oracle_price, -7)
    await admin_clearing_house.initialize_perp_market(
        oracle, 
        init_reserves, 
        init_reserves, 
        60, 
        int(peg), 
        OracleSource.PYTH(), 
        # default is 5x
        margin_ratio_initial=MARGIN_PRECISION // init_leverage if init_leverage else 2000
    )

    if spread is not None:
        await admin_clearing_house.update_perp_market_curve_update_intensity(i, 100)
        await admin_clearing_house.update_perp_market_base_spread(i, spread)

    await admin_clearing_house.update_perp_market_max_fill_reserve_fraction(i, 1)
    await admin_clearing_house.update_perp_market_step_size_and_tick_size(i, int(AMM_RESERVE_PRECISION/1e4), 1)

    return oracle_price

async def run_trial(protocol_path, events, markets, trial_outpath, oracle_guard_rails=None, spread=None):
    print('trial_outpath:', trial_outpath)
    print('protocol path:', protocol_path)

    df_row_index = 0
    workspace = create_workspace(protocol_path)
    program: Program = workspace["clearing_house"]
    oracle_program: Program = workspace["pyth"]
    provider: Provider = program.provider

    admin_clearing_house, usdc_mint = await setup_bank(program)

    # state modification
    await admin_clearing_house.update_perp_auction_duration(0)
    await admin_clearing_house.update_lp_cooldown_time(0)    

    if oracle_guard_rails is not None:
        await admin_clearing_house.update_oracle_guard_rails(oracle_guard_rails)

    # setup the markets
    init_leverage = 11
    n_markets = len(markets) 
    last_oracle_prices = []

    for i, market in enumerate(markets):
        oracle_price = await setup_market(
            admin_clearing_house, 
            oracle_program, 
            market, 
            i,
            init_leverage, 
            oracle_guard_rails, 
            spread
        )
        last_oracle_prices.append(oracle_price)

    # save initial state 
    await save_state(program, trial_outpath)

    start = time.time()

    # initialize users + deposits
    users, liquidator_index = await airdrop_sol_users(provider, events, trial_outpath)
    user_chs, _user_chus, init_total_collateral = await setup_usdc_deposits(events, program, usdc_mint, users, liquidator_index)

    liquidator = Liquidator(user_chs, n_markets, liquidator_index)

    ixs_log = []
    slot_log = []
    err_log = []
    ix_name_log = []

    # process events 
    for i in tqdm(range(len(events))):
        sys.stdout.flush()
        event = events.iloc[i]

        ix_args = None
        ix: TransactionInstruction
        if event.event_name == DepositCollateralEvent._event_name:
            continue

        elif event.event_name == OpenPositionEvent._event_name: 
            event = Event.deserialize_from_row(OpenPositionEvent, event)
            print(f'=> {event.user_index} opening position...')
            assert event.user_index in user_chs, 'user doesnt exist'

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch, init_leverage, oracle_program, adjust_oracle_pre_trade=False)

            if ix is None:
                continue

            from client.instructions.place_and_take import layout
            identifier = b"P\xfb\x17\xf1\x93\xed\x87\x92"
            ix_args = parse_ix_args(ix[1], layout, identifier) # [1] bc we increase the compute too
            order_params = dict(ix_args.pop('params'))
            order_params.pop('_io')
            ix_args['params'] = order_params

        elif event.event_name == ClosePositionEvent._event_name: 
            # dont close so we have stuff to settle at end of sim
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
            # event.token_amount = int(event.token_amount * AMM_RESERVE_PRECISION / 1e13)

            ix = await event.run_sdk(ch)

            from client.instructions.add_perp_lp_shares import layout
            identifier = b"8\xd18\xc5w\xfe\xbcu"
            ix_args = parse_ix_args(ix, layout, identifier)

        elif event.event_name == removeLiquidityEvent._event_name:
            event = Event.deserialize_from_row(removeLiquidityEvent, event)
            print(f'=> {event.user_index} removing liquidity...')
            assert event.user_index in user_chs, 'user doesnt exist'
            event.lp_token_amount = -1

            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)
            if ix is None: 
                continue

            from client.instructions.remove_perp_lp_shares import layout
            identifier = b"\xd5Y\xd9\x12\xa075\x8d"
            ix_args = parse_ix_args(ix, layout, identifier)

        elif event.event_name == SettlePnLEvent._event_name:
            event = Event.deserialize_from_row(SettlePnLEvent, event)
            print(f'=> {event.user_index} settle pnl...')
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)

        elif event.event_name == SettleLPEvent._event_name: 
            event = Event.deserialize_from_row(SettleLPEvent, event)
            print(f'=> {event.user_index} settle lp...')
            ch: SDKClearingHouse = user_chs[event.user_index]
            ix = await event.run_sdk(ch)

            from client.instructions.settle_lp import layout
            identifier = b"\x9b\xe7tqa\xe5\x8b\x8d"
            ix_args = parse_ix_args(ix, layout, identifier)
        
        elif event.event_name == oraclePriceEvent._event_name: 
            event = Event.deserialize_from_row(oraclePriceEvent, event)
            event.slot = (await provider.connection.get_slot())['result']
            print(f'=> adjusting oracle: {event.price}')
            await event.run_sdk(program, oracle_program)

        elif event.event_name == 'liquidate':
            print('=> liquidating...')
            await liquidator.liquidate_loop()
            continue
        
        elif event.event_name == NullEvent._event_name: 
            continue
        else:
            raise NotImplementedError

        # try to liquidate traders after each timestep 
        await liquidator.liquidate_loop()

        if ix_args is not None:
            slot = (await provider.connection.get_slot())['result']
            ixs_log.append(ix_args)
            slot_log.append(slot)
            ix_name_log.append(event._event_name)

            from solana.rpc.core import RPCException
            from anchorpy.error import ProgramError
            from anchorpy.program.core import _parse_idl_errors
            idl_errors = _parse_idl_errors(program.idl)

            from termcolor import colored
            try:
                if event._event_name == SettleLPEvent._event_name:
                    await ch.send_ixs(ix, signers=[])
                else:
                    await ch.send_ixs(ix)
                err_log.append('')

            except RPCException as e:
                err_log.append(e.args)
                print(colored(f'\n\n {event._event_name} failed... \n\n', "red"))
                print(e.args)

    pd.DataFrame({
        'slot': slot_log,
        'ix_name': ix_name_log,
        'ix_args': ixs_log,
        'errors': err_log,
    }).to_csv(f"./{trial_outpath}/ix_logs.csv", index=False)

    print('delisting market...')
    # get
    slot = (await provider.connection.get_slot())['result']
    dtime: int = (await provider.connection.get_block_time(slot))['result']

    # + N seconds
    seconds_time = 2
    for i in range(n_markets):
        await admin_clearing_house.update_perp_market_expiry(i, dtime + seconds_time)
    
    # close out all the LPs 
    routines = []
    for i in range(n_markets):
        for (_, ch) in user_chs.items():
            position = await ch.get_user_position(i)
            if position is None: 
                continue
            if position.lp_shares > 0:
                print(f'removing {position.lp_shares} lp shares...')
                routines.append(
                    ch.remove_liquidity(position.lp_shares, position.market_index)
                )
    await asyncio.gather(*routines)

    # settle expired market
    time.sleep(seconds_time)
    for i in range(n_markets):
        await admin_clearing_house.settle_expired_market(i)
    await save_state(program, trial_outpath, df_row_index, user_chs)
    df_row_index+=1

    for i in range(n_markets):
        market = await get_perp_market_account(
            program, i
        )
        print(
            'market expiry_price vs twap/price', 
            market.expiry_price, 
            market.amm.historical_oracle_data.last_oracle_price_twap,
            market.amm.historical_oracle_data.last_oracle_price
        )

    # liquidate em + resolve bankrupts
    await liquidator.liquidate_loop()

    # cancel open orders
    routines = []
    for (i, ch) in user_chs.items():
        position = await ch.get_user_position(0)
        if position is not None and position.open_orders > 0:
            routines.append(
                ch.cancel_order()
            )

    await save_state(program, trial_outpath, df_row_index, user_chs)
    df_row_index += 1

    await asyncio.gather(*routines)

    # settle expired positions 
    print('settling expired positions')

    for i in range(n_markets):
        number_positions = 0
        for (_, ch) in user_chs.items():
            position = await ch.get_user_position(i)
            if position is None: 
                continue
            number_positions += 1
        print('number of positions:', number_positions)

        market = await get_perp_market_account(program, i)
        print(
            'net long/short',
            market.amm.base_asset_amount_long, 
            market.amm.base_asset_amount_short, 
            market.number_of_users, 
        )

    from termcolor import colored
    for i in range(n_markets):
        routines = []
        success = False
        attempt = -1
        user_withdraw_count = 0
        n_users = len(list(user_chs.keys()))
        last_oracle_price = last_oracle_prices[i]

        while not success:
            attempt += 1
            success = True
            user_count = 0
            user_withdraw_count = 0

            print(colored(f' =>>>>>> attempt {attempt}', "blue"))
            for (_, ch) in user_chs.items():
                position = await ch.get_user_position(i)

                # dont let oracle go stale
                slot = (await provider.connection.get_slot())['result']
                market = await get_perp_market_account(program, i)
                await set_price_feed_detailed(oracle_program, market.amm.oracle, last_oracle_price, 0, slot)

                if position is None: 
                    user_count += 1
                else:
                    try:
                        settling_position = await ch.get_user_position(i)
                        scaled_balance = (await ch.get_user()).spot_positions[0].scaled_balance
                        print('user', i, str(ch.authority), ': ', '$',scaled_balance/SPOT_BALANCE_PRECISION)
                        print('settling position:', settling_position)
                        await ch.settle_pnl(ch.authority, i)
                        user_count += 1
                        print(colored(f'     *** settle expired position successful {user_count}/{n_users} ***   ', "green"))
                        await save_state(program, trial_outpath, df_row_index, user_chs)
                        df_row_index+=1
                    except Exception as e:
                        if "0x17e2" in e.args[0]['message']: # pool doesnt have enough 
                            print(colored(f'     *** settle expired position failed... ***   ', "red"))
                            print(e.args)
                            success = False
                        elif "0x17c0" in e.args[0]['message']: # pool doesnt have enough 
                            print(colored(f'     *** settle expired position failed InsufficientCollateralForSettlingPNL... ***   ', "red"))
                            print(e.args)
                            success = False
                        else: 
                            raise Exception(e)

                try:
                    # try to withdraw all you can
                    print(f'=> user {i} withdrawing...')
                    await ch.withdraw(
                        int(1e10 * 1e6), 
                        0, 
                        ch.usdc_ata.public_key,
                        True
                    )
                    print(colored(f'     *** user withdraw successful {user_withdraw_count}/{n_users} ***   ', "green"))
                    user_withdraw_count+=1
                    await save_state(program, trial_outpath, df_row_index, user_chs)
                except Exception as e:
                    print(e)
                    print(colored(f'     *** user withdraw failed {user_withdraw_count}/{n_users} ***   ', "red"))
                    pass
                
                market = await get_perp_market_account(program, i)
                print(
                    'net long/short',
                    market.amm.base_asset_amount_long, 
                    market.amm.base_asset_amount_short, 
                    market.number_of_users, 
                )
    for i in range(n_markets):
        for (_, ch) in user_chs.items():
            position = await ch.get_user_position(i)
            if position is None: 
                continue
            print(position)

    # skip for now
    # await admin_clearing_house.settle_expired_market_pools_to_revenue_pool(0)

    market = await get_perp_market_account(program, i)
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

async def main(protocol_path, experiments_folder, geyser_path, trial):
    events = pd.read_csv(f"{experiments_folder}/events.csv")

    no_oracle_guard_rails = OracleGuardRails(
        price_divergence=PriceDivergenceGuardRails(1, 1), 
        validity=ValidityGuardRails(10, 10, 100, 100),
        use_for_liquidations=True
    )

    trial_guard_rails = None
    spread = None

    if 'spread_250' in trial:
        print('spread 250 activated')
        spread = 250
        trial_guard_rails = no_oracle_guard_rails
   
    if 'spread_1000' in trial:
        print('spread 1000 activated')
        spread = 1000
        trial_guard_rails = no_oracle_guard_rails

    if 'no_oracle_guards' in trial:
        print('no_oracle_guard_rails activated')
        trial_guard_rails = no_oracle_guard_rails

    # read and load initial clearing house state (thats all we use chs.csv for...)
    with open(f'{experiments_folder}/markets_json.csv', 'r') as f:
        markets = json.load(f)

    experiment_name = Path(experiments_folder).stem
    output_path = Path(f'{experiments_folder}/../../results/{experiment_name}/trial_{trial}')
    output_path.mkdir(exist_ok=True, parents=True)

    setup_run_info(str(output_path), protocol_path, '')

    val = LocalValidator(protocol_path, geyser_path)
    val.start()
    try:
        await run_trial(
            protocol_path, 
            events, 
            markets, 
            output_path, 
            trial_guard_rails, 
            spread
        )
    finally:
        val.stop()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', type=str, required=True)
    parser.add_argument('--protocol', type=str, required=False, default='../driftpy/protocol-v2')
    parser.add_argument('--geyser', type=str, required=False, default='../solana-accountsdb-plugin-postgres')

    # trials = ['no_oracle_guards', 'spread_250', 'spread_1000', 'oracle_guards',]
    parser.add_argument('-t', '--trial', type=str, required=False, default='')

    args = parser.parse_args()

    try: 
        import asyncio
        asyncio.run(main(args.protocol, args.events, args.geyser, args.trial))
    finally:
        pass

