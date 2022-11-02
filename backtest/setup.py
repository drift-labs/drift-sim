import pandas as pd 
import numpy as np 

from solana.rpc import commitment
from solana.keypair import Keypair

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

from driftpy.setup.helpers import _create_mint, mock_oracle, _airdrop_user, set_price_feed, set_price_feed_detailed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_ata_tx
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.math.amm import calculate_mark_price_amm
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account

from anchorpy import Provider, Program, create_workspace, WorkspaceType
from sim.driftsim.clearing_house.state.market import SimulationAMM, SimulationMarket
import pprint
import os
import json

from driftpy.setup.helpers import _create_user_ata_tx
from solana.keypair import Keypair

from subprocess import Popen
import datetime
import subprocess
from solana.transaction import Transaction
import asyncio
from tqdm import tqdm
from helpers import view_logs

from typing import Optional, Union, cast, Dict
import json
from pathlib import Path
from solana.publickey import PublicKey
from anchorpy.program.core import Program
from anchorpy.provider import Provider
from anchorpy.idl import Idl, _Metadata
WorkspaceType = Dict[str, Program]
import time 
import signal

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
        assert process.poll() == 0, 'anchor build failed'

        process = Popen("bash setup.sh".split(' '), cwd=self.geyser_path)
        process.wait()
        assert process.poll() == 0, 'setting up localnet (setup.sh) failed'

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
        print(file.stem, id)
        
        program = Program(idl, id, provider)
        result[idl.name] = program
        
    return result


async def setup_deposits(
    events: pd.DataFrame, 
    program: Program, 
    spot_mints: list[Keypair], 
    users: list, 
    liquidator_index: int
):
    user_chs = {}
    user_chus = {}
    init_total_collateral = 0 

    # deposit all at once for speed 
    deposit_amounts = {}
    mint_amounts = {}
    spot_markets = {}
    user_indexs = []

    for i in range(len(spot_mints)):
        spot_markets[i] = {
            'mints': {},
            'deposits': {}
        }

    for i in tqdm(range(len(events))):
        event = events.iloc[i]
        if event.event_name == DepositCollateralEvent._event_name:
            event = Event.deserialize_from_row(DepositCollateralEvent, event)

            spot_market_index = event.spot_market_index

            sm = spot_markets[spot_market_index]
            mints = sm['mints']
            deposits = sm['deposits']

            if event.user_index not in user_indexs:
                user_indexs.append(event.user_index)

            deposits[event.user_index] = deposits.get(event.user_index, 0) + event.deposit_amount
            mints[event.user_index] = mints.get(event.user_index, 0) + event.mint_amount

    # dont let the liquidator get liq'd 
    for i in range(len(spot_mints)):
        spot_markets[i]['deposits'][liquidator_index] = 1_000_000 * QUOTE_PRECISION
        spot_markets[i]['mints'][liquidator_index] = 0
    user_indexs.append(liquidator_index)

    for spot_market_index in range(len(spot_mints)):
        mint = spot_mints[spot_market_index]
        deposit_amounts = spot_markets[spot_market_index]['deposits']
        mint_amounts = spot_markets[spot_market_index]['mints']

        for user_index in user_indexs:
            deposit_amount = deposit_amounts.get(user_index, 0)
            mint_amount = mint_amounts.get(user_index, 0)
            user_kp = users[user_index][0]
            print(f'=> user {user_index} depositing in spot {spot_market_index}: {deposit_amount / QUOTE_PRECISION:,.0f}...')

            await setup_user(
                user_chs,
                user_chus,
                user_index, 
                program, 
                mint, 
                spot_market_index,
                deposit_amount, 
                mint_amount,
                user_kp
            )

            # track collateral 
            init_total_collateral += deposit_amount + mint_amount

    return user_chs, user_chus, init_total_collateral

async def setup_user(
    user_chs,
    user_chus,
    user_index, 
    program: Program, 
    usdc_mint, 
    spot_market_index,
    deposit_amount, 
    mint_amount,
    user_kp
):
    # rough draft
    instructions = []
    signers = []
    provider: Provider = program.provider

    # initialize user 
    if user_index not in user_chs:
        user_clearing_house = SDKClearingHouse(program, user_kp)
        await user_clearing_house.intialize_user()
        user_clearing_house.user_index = user_index
    else: 
        user_clearing_house = user_chs[user_index]

    ata_kp = Keypair()
    ata_tx = await _create_user_ata_tx(
        ata_kp, 
        provider, 
        usdc_mint, 
        user_clearing_house.authority
    )
    user_clearing_house.spot_market_atas[spot_market_index] = ata_kp.public_key
    if spot_market_index == 0:
        user_clearing_house.ata = ata_kp.public_key

    instructions += ata_tx.instructions

    user_chs[user_index] = user_clearing_house
    user_chus[user_index] = ClearingHouseUser(user_clearing_house)

    # add fundings 
    mint_tx = _mint_usdc_tx(
        usdc_mint, 
        provider, 
        int(deposit_amount + mint_amount), 
        ata_kp.public_key
    )
    instructions += mint_tx.instructions
    signers += [provider.wallet.payer, ata_kp]

    if deposit_amount > 0:
        instructions += [
            await user_clearing_house.get_deposit_collateral_ix(
                int(deposit_amount), 
                spot_market_index, 
                ata_kp.public_key
            )
        ]
        signers += user_clearing_house.signers

    tx = Transaction()
    [tx.add(ix) for ix in instructions]
    routine = provider.send(tx, signers)

    return await routine

async def airdrop_sol_users(provider, events, user_path):
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
    with open(user_path, 'w') as f:
        json.dump(json_users, f)

    for user, tx_sig in tqdm(users.values()):
        await provider.connection.confirm_transaction(tx_sig, sleep_seconds=0.1)
    
    return users, liquidator_index

async def setup_spot_market(
    admin_clearing_house: Admin, 
    oracle_program: Program, 
    spot_market: dict, 
    spot_market_index: int,
):
    i = spot_market_index
    oracle_price = spot_market['init_price']

    print(f"=> initializing spot market {i}...")
    print('\t> init oracle price:', oracle_price)

    oracle = await mock_oracle(oracle_program, oracle_price, -7)
    mint = await _create_mint(admin_clearing_house.program.provider)

    optimal_util = SPOT_WEIGHT_PRECISION // 2
    optimal_weight = int(SPOT_WEIGHT_PRECISION * 20)
    max_rate = int(SPOT_WEIGHT_PRECISION * 50)
    
    init_weight = int(SPOT_WEIGHT_PRECISION * 8 / 10)
    main_weight = int(SPOT_WEIGHT_PRECISION * 9 / 10)

    init_liab_weight = int(SPOT_WEIGHT_PRECISION * 12 / 10)
    main_liab_weight = int(SPOT_WEIGHT_PRECISION * 11 / 10)

    await admin_clearing_house.initialize_spot_market(
        mint.public_key, 
        oracle=oracle, 
        optimal_utilization=optimal_util, 
        optimal_rate=optimal_weight, 
        max_rate=max_rate,
        oracle_source=OracleSource.PYTH(),
        initial_asset_weight=init_weight, 
        maintenance_asset_weight=main_weight, 
        initial_liability_weight=init_liab_weight, 
        maintenance_liability_weight=main_liab_weight
    )

    return mint

async def setup_market(
    admin_clearing_house: Admin, 
    oracle_program: Program, 
    market: dict, 
    market_index: int,
    init_leverage: int, 
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

    margin_ratio = MARGIN_PRECISION // init_leverage if init_leverage else 2000
    margin_ratio_main = margin_ratio - 200
    print('\t> margin ratio (init, main):', margin_ratio, margin_ratio_main)

    await admin_clearing_house.initialize_perp_market(
        oracle, 
        init_reserves, 
        init_reserves, 
        60, 
        int(peg), 
        OracleSource.PYTH(), 
        # default is 5x
        margin_ratio_initial=margin_ratio,
        margin_ratio_maintenance=margin_ratio_main
    )

    if spread is not None:
        await admin_clearing_house.update_perp_market_curve_update_intensity(i, 100)
        await admin_clearing_house.update_perp_market_base_spread(i, spread)

    await admin_clearing_house.update_perp_market_max_fill_reserve_fraction(i, 1)
    await admin_clearing_house.update_perp_market_step_size_and_tick_size(i, int(AMM_RESERVE_PRECISION/1e4), 1)

    return oracle_price

async def setup_bank(
    program: Program,
):
    # init usdc mint
    usdc_mint = await _create_mint(program.provider)

    # init state + bank + market 
    clearing_house = Admin(program)
    resp = await clearing_house.initialize(usdc_mint.public_key, True)

    # need this or else says clearing_house hasnt been initialized yet when we init spot
    await view_logs(resp, program.provider, print=False)

    await clearing_house.initialize_spot_market(usdc_mint.public_key)

    return clearing_house, usdc_mint
