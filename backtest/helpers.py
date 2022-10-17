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

from driftpy.setup.helpers import _create_usdc_mint, mock_oracle, _airdrop_user, set_price_feed, set_price_feed_detailed, adjust_oracle_pretrade, _mint_usdc_tx, _create_user_usdc_ata_tx
from driftpy.admin import Admin
from driftpy.types import OracleSource

from sim.events import * 
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.math.amm import calculate_mark_price_amm
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.accounts import get_perp_market_account, get_spot_market_account, get_user_account, get_state_account

from anchorpy import Provider, Program, create_workspace, WorkspaceType
from programs.clearing_house.state.market import SimulationAMM, SimulationMarket
import pprint
import os
import json

from driftpy.setup.helpers import _create_user_usdc_ata_tx
from solana.keypair import Keypair

from subprocess import Popen
import datetime
import subprocess

def get_git_revision_hash(path=None) -> str:
    result = None
    if path is None:
        result = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    else:
        result = subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD']).decode('ascii').strip()

    is_dirty = get_git_dirty()
    if is_dirty:
        result+='-dirty'

    return result

def get_git_revision_short_hash(path=None) -> str:
    output = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    is_dirty = get_git_dirty()
    if is_dirty:
        output+='-dirty'
    return output

def get_git_dirty() -> str:
    #If the exit code is 0, then there were no differences.
    return subprocess.call(['git', 'diff-index', '--quiet', 'HEAD'])

def setup_run_info(sim_path, protocol_path, ch_name):
    os.makedirs(sim_path, exist_ok=True)
    maintenant = datetime.datetime.utcnow()
    maintenant_str = maintenant.strftime("%Y/%m/%d %H:%M:%S UTC")
    sim_git_commit = get_git_revision_hash()
    protocol_git_commit = get_git_revision_hash(protocol_path)

    run_data = {
        'run_time': maintenant_str, 
        'sim_git_commit': sim_git_commit,
        'protocol_git_commit': protocol_git_commit,
        'path': sim_path,
        'name': ch_name,
    }
    with open(os.path.join(sim_path, 'run_info.json'), 'w') as f:
        json.dump(run_data, f)

def serialize_perp_market(market: PerpMarket):
    data = market.__dict__
    d2 = market.amm.__dict__  
    d3 = market.amm.historical_oracle_data.__dict__
    data.pop('padding')
    data.update(d2)
    data.update(d3)
    result = pd.DataFrame(data, index=list(range(6))).head(1)

    return result 

def human_amm_df(df):
    bool_fields = [ 'last_oracle_valid']
    enum_fields = ['oracle_source']
    pure_fields = ['last_update_slot', 'long_intensity_count', 'short_intensity_count', 
    'curve_update_intensity', 'amm_jit_intensity'
    ]
    reserve_fields = [
        'base_asset_reserve', 'quote_asset_reserve', 'min_base_asset_reserve', 'max_base_asset_reserve', 'sqrt_k',
        'ask_base_asset_reserve', 'ask_quote_asset_reserve', 'bid_base_asset_reserve', 'bid_quote_asset_reserve',
        'terminal_quote_asset_reserve', 'base_asset_amount_long', 'base_asset_amount_short', 'base_asset_amount_with_amm', 'base_asset_amount_with_unsettled_lp',
        'user_lp_shares', 'min_order_size', 'max_position_size',
        ]
    pct_fields = ['base_spread','long_spread', 'short_spread', 'max_spread', 'concentration_coef',
    'last_oracle_reserve_price_spread_pct',
    'last_oracle_conf_pct',
    'utilization_twap',
    
    ]
    funding_fields = ['cumulative_funding_rate_long', 'cumulative_funding_rate_short', 'last_funding_rate', 'last_funding_rate_long', 'last_funding_rate_short', 'last24h_avg_funding_rate']
    quote_asset_fields = ['total_fee', 'total_mm_fee', 'total_exchange_fee', 'total_fee_minus_distributions',
    'total_fee_withdrawn', 'total_liquidation_fee', 'cumulative_social_loss', 'net_revenue_since_last_funding',
    'quote_asset_amount_long', 'quote_asset_amount_short', 'quote_entry_amount_long', 'quote_entry_amount_short',
    'volume24h', 'long_intensity_volume', 'short_intensity_volume',
    'total_spot_fee',
    ]
    time_fields = ['last_trade_ts', 'last_mark_price_twap_ts', 'last_oracle_price_twap_ts',]
    duration_fields = ['lp_cooldown_time', 'funding_period']
    px_fields = [
        'last_oracle_normalised_price',
        'order_tick_size',
        'last_bid_price_twap', 'last_ask_price_twap', 'last_mark_price_twap', 'last_mark_price_twap5min',
    'peg_multiplier',
    'mark_std',
    'last_oracle_price_twap', 'last_oracle_price_twap5min',
    'last_oracle_price', 'last_oracle_conf', 
    
    ]
    balance_fields = ['scaled_balance', 'deposit_balance', 'borrow_balance']

    for col in df.columns:
        # if col in enum_fields or col in bool_fields:
        #     pass
        # else if col in duration_fields:
        #     pass
        # else if col in pure_fields:
        #     pass
        if col in reserve_fields:
            df[col] /= 1e9
        elif col in funding_fields:
            df[col] /= 1e9
        elif col in quote_asset_fields:
            df[col] /= 1e6
        elif col in pct_fields:
            df[col] /= 1e6
        elif col in px_fields:
            df[col] /= 1e6
        # else if col in time_fields:
        #     pass
        elif col in balance_fields:
            df[col] /= 1e9
            
    return df

def human_market_df(df):
    enum_fields = ['status', 'contract_tier', '']
    pure_fields = ['number_of_users', 'market_index', 'next_curve_record_id', 'next_fill_record_id', 'next_funding_rate_record_id']
    pct_fields = ['imf_factor', 'unrealized_pnl_imf_factor', 'liquidator_fee', 'if_liquidation_fee']
    wgt_fields = ['initial_asset_weight', 'maintenance_asset_weight',
    
    'initial_liability_weight', 'maintenance_liability_weight',
    'unrealized_pnl_initial_asset_weight', 'unrealized_pnl_maintenance_asset_weight']
    margin_fields = ['margin_ratio_initial', 'margin_ratio_maintenance']
    px_fields = [
        'expiry_price',
        'last_oracle_normalised_price',
        'order_tick_size',
        'last_bid_price_twap', 'last_ask_price_twap', 'last_mark_price_twap', 'last_mark_price_twap5min',
    'peg_multiplier',
    'mark_std',
    'last_oracle_price_twap', 'last_oracle_price_twap5min',
    
    ]
    time_fields = ['last_trade_ts', 'expiry_ts', 'last_revenue_withdraw_ts']
    balance_fields = ['scaled_balance', 'deposit_balance', 'borrow_balance']
    quote_fields = [
        
        'total_spot_fee', 
        'unrealized_pnl_max_imbalance', 'quote_settled_insurance', 'quote_max_insurance', 
    'max_revenue_withdraw_per_period', 'revenue_withdraw_since_last_settle', ]
    token_fields = ['borrow_token_twap', 'deposit_token_twap', 'withdraw_guard_threshold', 'max_token_deposits']
    interest_fields = ['cumulative_deposit_interest', 'cumulative_borrow_interest']

    for col in df.columns:
        # if col in enum_fields:
        #     pass
        # elif col in pure_fields:
        #     pass
        if col in pct_fields:
            df[col] /= 1e6
        elif col in px_fields:
            df[col] /= 1e6
        elif col in margin_fields:
            df[col] /= 1e4
        elif col in wgt_fields:
            df[col] /= 1e4
        # elif col in time_fields:
        #     pass
        elif col in quote_fields:
            df[col] /= 1e6
        elif col in balance_fields:
            df[col] /= 1e9
        elif col in interest_fields:
            df[col] /= 1e10
        elif col in token_fields:
            df[col] /= 1e6 #todo   

    return df
    
def serialize_perp_market_2(market: PerpMarket):

    market_df = pd.json_normalize(market.__dict__).drop(['amm', 'insurance_claim', 'pnl_pool'],axis=1).pipe(human_market_df)
    market_df.columns = ['market.'+col for col in market_df.columns]

    amm_df= pd.json_normalize(market.amm.__dict__).drop(['historical_oracle_data', 'fee_pool'],axis=1).pipe(human_amm_df)
    amm_df.columns = ['market.amm.'+col for col in amm_df.columns]

    amm_hist_oracle_df= pd.json_normalize(market.amm.historical_oracle_data.__dict__).pipe(human_amm_df)
    amm_hist_oracle_df.columns = ['market.amm.historical_oracle_data.'+col for col in amm_hist_oracle_df.columns]

    market_amm_pool_df = pd.json_normalize(market.amm.fee_pool.__dict__).pipe(human_amm_df)
    market_amm_pool_df.columns = ['market.amm.fee_pool.'+col for col in market_amm_pool_df.columns]

    market_if_df = pd.json_normalize(market.insurance_claim.__dict__).pipe(human_market_df)
    market_if_df.columns = ['market.insurance_claim.'+col for col in market_if_df.columns]

    market_pool_df = pd.json_normalize(market.pnl_pool.__dict__).pipe(human_amm_df)
    market_pool_df.columns = ['market.pnl_pool.'+col for col in market_pool_df.columns]


    result_df = pd.concat([market_df, amm_df, amm_hist_oracle_df, market_amm_pool_df, market_if_df, market_pool_df],axis=1)
    return result_df

def serialize_spot_market(spot_market: SpotMarket):
    spot_market_df = pd.json_normalize(spot_market.__dict__).drop([
        'historical_oracle_data', 'historical_index_data',
        'insurance_fund', # todo
        'spot_fee_pool', 'revenue_pool'
        ], axis=1)
    spot_market_df.columns = ['spot_market.'+col for col in spot_market_df.columns]

    hist_oracle_df= pd.json_normalize(spot_market.historical_oracle_data.__dict__).pipe(human_amm_df)
    hist_oracle_df.columns = ['spot_market.historical_oracle_data.'+col for col in hist_oracle_df.columns]

    hist_index_df= pd.json_normalize(spot_market.historical_index_data.__dict__).pipe(human_amm_df)
    hist_index_df.columns = ['spot_market.historical_index_data.'+col for col in hist_index_df.columns]


    market_pool_df = pd.json_normalize(spot_market.revenue_pool.__dict__).pipe(human_amm_df)
    market_pool_df.columns = ['spot_market.revenue_pool.'+col for col in market_pool_df.columns]


    market_fee_df = pd.json_normalize(spot_market.spot_fee_pool.__dict__).pipe(human_amm_df)
    market_fee_df.columns = ['spot_market.spot_fee_pool.'+col for col in market_fee_df.columns]

    result_df = pd.concat([spot_market_df, hist_oracle_df, hist_index_df, market_pool_df, market_fee_df],axis=1)
    return result_df

async def save_state(program, experiments_folder, event_i, user_chs):
    state: State = await get_state_account(program)

    for spot_market_index in range(0, state.number_of_spot_markets):
        spot_market: PerpMarket = await get_spot_market_account(program, spot_market_index)
        print(str(spot_market.status))
        df = serialize_spot_market(spot_market)
        outfile = f"./{experiments_folder}/spot_market"+str(spot_market_index)+".csv"
        if event_i > 0:
            df.to_csv(outfile, mode="a", index=False, header=False)
        else:
            df.to_csv(outfile, index=False)

    for market_index in range(0, state.number_of_markets):
        market: PerpMarket = await get_perp_market_account(program, market_index)
        df = serialize_perp_market_2(market)
        outfile = f"./{experiments_folder}/perp_market"+str(market_index)+".csv"
        if event_i > 0:
            df.to_csv(outfile, mode="a", index=False, header=False)
        else:
            df.to_csv(outfile, index=False)

    # all_users = await program.account["User"].all()
    all_user_stats = {
        'total_collateral':[],
        # 'free_collateral':[],
        # 'leverage':[],
        # 'get_unrealized_pnl_0':[],
        # 'get_spot_market_asset_value':[],
        # 'get_spot_market_liability':[],
        # 'get_margin_requirement':[],
        # 'can_be_liquidated':[],
        # 'get_total_perp_positon':[]
    }
    for (i, user_ch) in user_chs.items():
        upk = (user_ch.authority)
        user_account: PerpMarket = await get_user_account(program, upk, 0)

        chu = ClearingHouseUser(user_ch, user_ch.authority)
        all_user_stats['total_collateral'].append(await chu.get_total_collateral())
        # all_user_stats['free_collateral'].append(chu.get_free_collateral())
        # all_user_stats['get_unrealized_pnl'].append(chu.get_unrealized_pnl())
        # all_user_stats['get_spot_market_asset_value'].append(chu.get_spot_market_asset_value())
        # all_user_stats['get_spot_market_liability'].append(chu.get_spot_market_liability())
        # all_user_stats['get_margin_requirement'].append(chu.get_margin_requirement())
        # all_user_stats['can_be_liquidated'].append(chu.can_be_liquidated())
        # all_user_stats['get_total_perp_positon'].append(chu.get_total_perp_positon())
        # all_user_stats['leverage'].append(chu.get_leverage())

        uu = user_account.__dict__
        uu.pop('orders')
        uu.pop('name')
        uu.pop('padding')
        df = pd.DataFrame(uu, index=list(range(8))).head(1) #todo show all positions
        outfile = f"./{experiments_folder}/result_user_"+str(i)+".csv"
        if event_i > 0:
            df.to_csv(outfile, mode="a", index=False, header=False)
        else:
            df.to_csv(outfile, index=False)

    all_user_stats_df = pd.DataFrame([sum(all_user_stats['total_collateral'])],
         columns=['total_collateral'], index=[0])
    outfile = f"./{experiments_folder}/all_user_stats.csv"
    if event_i > 0:
        all_user_stats_df.to_csv(outfile, mode="a", index=False, header=False)
    else:
        all_user_stats_df.to_csv(outfile, index=False)

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



async def setup_market(
    clearing_house: Admin,
    market: SimulationMarket,
    workspace: WorkspaceType
):
    amm = market.amm
    oracle = await mock_oracle(workspace["pyth"], 1, -7)

    await clearing_house.initialize_perp_market(
        oracle, 
        int(amm.base_asset_reserve), 
        int(amm.quote_asset_reserve), 
        int(amm.funding_period), 
        int(amm.peg_multiplier), 
        OracleSource.Pyth(), 
    )

    # update durations
    await clearing_house.update_auction_duration(0, 0)
    await clearing_house.update_lp_cooldown_time(0, 0)
    await clearing_house.update_max_base_asset_amount_ratio(1, 0)
    await clearing_house.update_perp_step_size_and_tick_size(0, 1, 1)
    
    # add a spread 
    if amm.base_spread > 0:
        print('setting spread..')
        await clearing_house.update_market_base_spread(amm.base_spread, 0)

    return oracle

async def setup_bank(
    program: Program,
):
    # init usdc mint
    usdc_mint = await _create_usdc_mint(program.provider)

    # init state + bank + market 
    clearing_house = Admin(program)
    resp = await clearing_house.initialize(usdc_mint.public_key, True)
    await view_logs(resp, program.provider)
    await clearing_house.initialize_spot_market(usdc_mint.public_key)

    return clearing_house, usdc_mint

async def view_logs(
    sig,
    provider: Provider
):
    provider.connection._commitment = commitment.Confirmed 
    try: 
        await provider.connection.confirm_transaction(sig, commitment.Confirmed)
        logs = (await provider.connection.get_transaction(sig))["result"]["meta"]["logMessages"]
    finally:
        provider.connection._commitment = commitment.Processed 
    pprint.pprint(logs)