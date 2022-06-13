import pandas as pd
pd.options.plotting.backend = "plotly"

import sys
sys.path.insert(0, 'driftpy/src/')
import driftpy

import sys 
import driftpy
from tqdm import tqdm
from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction,
    calculate_peg_multiplier
)
from driftpy.math.repeg import calculate_repeg_cost
from driftpy.math.funding import calculate_long_short_funding
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl, calculate_position_funding_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price, calculate_bid_price, calculate_ask_price
from driftpy.math.user import *

import os
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PEG_PRECISION
from solana.publickey import PublicKey

import datetime
import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field
from driftpy.math.amm import calculate_price

from programs.clearing_house.state import * 
import multiprocessing

from sim.agents import * 
from sim.events import OpenPositionEvent, DepositCollateralEvent
from sim.helpers import random_walk_oracle, rand_heterosk_oracle, class_to_json
import pickle as cPickle

import subprocess

def get_git_revision_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()

def get_git_revision_short_hash() -> str:
    output = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    is_dirty = get_git_dirty()
    if is_dirty:
        output+='-dirty'
    return output


def get_git_dirty() -> str:
    #If the exit code is 0, then there were no differences.
    return subprocess.call(['git', 'diff-index', '--quiet', 'HEAD'])


def clearing_house_to_df(x: ClearingHouse):
    current_time = x.time
    market = x.markets[0]
    
    market_df = pd.json_normalize(market.__dict__).drop(['amm'],axis=1)
    amm_df = pd.json_normalize(market.amm.__dict__)
    
    oracle_price = amm_df['oracle'].values[0].get_price(current_time)
    
    mark_price = calculate_mark_price(market, oracle_price)
    bid_price = calculate_bid_price(market, oracle_price)
    ask_price = calculate_ask_price(market, oracle_price)
    peg = calculate_peg_multiplier(market.amm, oracle_price)
    wouldbe_peg_cost = calculate_repeg_cost(market, peg)[0]
    amm_df = amm_df.drop(['oracle'],axis=1)
    
    if x.users.get(0, None):
        user0: User = x.users[0]
        
        #todo
        # user0.collateral = user0.collateral_amount
        
        user_df = pd.json_normalize(user0.positions[0].__dict__)        
        user_df['collateral'] = user0.collateral
        user_df['m0_upnl'] = calculate_position_pnl(market, user0.positions[0])
        user_df['total_collateral'] = user_df['collateral'] +  user_df['m0_upnl'] #todo
        user_df['m0_ufunding'] = calculate_position_funding_pnl(market, user0.positions[0])
        user_df['free_collateral'] = get_free_collateral(user0, x.markets)
        user_df['margin_ratio'] = get_margin_ratio(user0, x.markets)
        user_df['total_position_value'] = get_total_position_value(user0.positions, x.markets)

        user_df.columns = ['u0_'+col for col in user_df.columns]
    else:
        user_df = pd.DataFrame()
    
    res_df = pd.concat([market_df, amm_df, user_df],axis=1)
    res_df['oracle_price'] = oracle_price
    res_df['mark_price'] = mark_price
    res_df['bid_price'] = bid_price
    res_df['ask_price'] = ask_price
    res_df['wouldbe_peg'] = peg/1e3

    long_funding, short_funding = calculate_long_short_funding(market)
    res_df['predicted_long_funding'] = long_funding
    res_df['predicted_short_funding'] = short_funding
    res_df['last_mid_price_twap'] = (res_df['last_bid_price_twap']+res_df['last_ask_price_twap'])/2

    res_df['wouldbe_peg_cost'] = wouldbe_peg_cost
    res_df['repeg_to_oracle_cost'] = calculate_repeg_cost(market, int(oracle_price*1e3))[0]

    for x in ['total_fee', 'total_mm_fees', 'total_exchange_fees', 'total_fee_minus_distributions']:
        res_df[x] /= 1e6

    res_df.index = [current_time]
    
    return res_df


def load_hist_oracle(market, outfile):
    oracle_prices = []
    for month in range(1,6):
        pid = 'dammHkt7jmytvbS3nHTxQNEcP59aE57nxwV21YdqEDN'
        url = 'https://drift-historical-data.s3.eu-west-1.amazonaws.com/program/%s/market/%s/trades/2022/%i' \
        % (pid, market, month)
        oracle_price = pd.read_csv(url)[['blockchainTimestamp', 'oraclePrice']]
        oracle_prices.append(oracle_price)

    luna_oracle_df = pd.concat(oracle_prices)
    luna_oracle_df.columns = ['timestamp', 'price']
    luna_oracle_df['price']/=1e10
    # luna_oracle_df.tail(10000).plot()
    luna_oracle_df['timestamp'] = luna_oracle_df['timestamp'].diff()\
    .apply(lambda x: x+1 if x==0 else x).fillna(0).cumsum()
    luna_oracle_df.to_csv(outfile, index=False)
    return luna_oracle_df

def setup_run_info(sim_path, ch_name):
    os.makedirs(sim_path, exist_ok=True)
    maintenant = datetime.datetime.utcnow()
    maintenant_str = maintenant.strftime("%Y/%m/%d %H:%M:%S UTC")
    git_commit = get_git_revision_short_hash()
    run_data = {
        'run_time': maintenant_str, 
        'git_commit': git_commit,
        'path': sim_path,
        'name': ch_name,
    }
    with open(os.path.join(sim_path, 'run_info.json'), 'w') as f:
        json.dump(run_data, f)

class DriftSim:
    def __init__(self, name, clearing_house=None, agents=None, ch_name=None):
        assert('sim-' in name)
        self.name = name

        # setup oracle 
        oracle_path = name + '/oracle_prices.csv'
        if not os.path.exists(oracle_path):
            load_hist_oracle('LUNA-PERP', oracle_path)
        oracle = Oracle(oracle_path)
        self.oracle = oracle

        if clearing_house is None:
            amm_params = dict(
                oracle=oracle, 
                base_asset_reserve=367621.62052551797 * 1e13, 
                quote_asset_reserve=367621.62052551797 * 1e13,
                funding_period=60*60,
                peg_multiplier=int(oracle.prices[0]*1e3),
                base_spread = 1e3
            )
            amm = AMM(**amm_params)
            market = Market(amm)

            fee_structure = FeeStructure(numerator=1, denominator=1000)
            clearing_house = ClearingHouse([market], fee_structure)
            self.clearing_house = clearing_house
        else:
            self.clearing_house = clearing_house

        if agents is None:
            arb_agent = Arb(
                intensity=1, 
                market_index=0,
                user_index=0, 
            )
            agents = [arb_agent]
            self.agents = agents
        else:
            self.agents = agents
        
        if ch_name is None:
            if clearing_house.name=='':
                count = 0
                default_ch_name = name+'/ch'+str(count)
                while os.path.exists(default_ch_name):
                    count+=1
                    default_ch_name = name+'/ch'+str(count)
                self.ch_name = default_ch_name
                ch_name = str(count)
            else:
                ch_name = str(clearing_house.name)
                self.ch_name = name+'/ch'+str(clearing_house.name)
        else:
            self.ch_name = name+'/ch'+str(ch_name)

        setup_run_info(self.ch_name, self.name)

    def run(self, debug=None):
        clearing_house, oracle, agents = self.clearing_house, self.oracle, self.agents
        simulation_results = {
            'events': [], 
            'clearing_houses': [],
        }
        start, end = oracle.get_timestamp_range()
        print('running simulation for %i timesteps' % (end-start))

        # timestamp 0 
        noop = NullEvent(timestamp=clearing_house.time)
        simulation_results['events'].append(noop)
        simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
        clearing_house.change_time(+1)

        # setup agents
        for agent in self.agents:        
            event_i = agent.setup(clearing_house)
            clearing_house = event_i.run(clearing_house)
            
            simulation_results['events'].append(event_i)
            simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
            
            clearing_house = clearing_house.change_time(+1)

        # run the simulation 
        print('running sim from timestamp', start,'to', end)
        for x in range(start, end):
            if x < clearing_house.time:
                print(f"skipping time step: {x} ... ch time: {clearing_house.time}")
                continue
            
            # run the agents at each timestep 
            for i, agent in enumerate(agents):
                event_i = agent.run(clearing_house)
                clearing_house = event_i.run(clearing_house)
                
                simulation_results['events'].append(event_i)
                simulation_results['clearing_houses'].append(copy.deepcopy(clearing_house))
                
                if debug == x:
                    print('debugging event #%i:' % x)
                    print(event_i)
                    print(clearing_house)
            
            clearing_house = clearing_house.change_time(1)
        
        self.simulation_results = simulation_results # save sim run results 
        return simulation_results

    def to_df(self, save=True):
        simulation_results = self.simulation_results
        SIM_NAME = self.ch_name
        
        # serialize clearing house state 
        json_chs = [
            ch.to_json() for ch in tqdm(simulation_results['clearing_houses'])
        ]
        result_df = pd.DataFrame(json_chs)

        if save:
            # serialize events 
            simulation_event_rows = [e.serialize_to_row() for e in simulation_results['events']]
            simulation_df = pd.DataFrame(simulation_event_rows)
            oracle = self.oracle

            # serialize oracles
            oracle_df = pd.DataFrame({'timestamp': oracle.timestamps, 'price': oracle.prices})

            oracle_df.to_csv(SIM_NAME+"/oracle_prices.csv", index=False)
            simulation_df.to_csv(SIM_NAME+"/events.csv", index=False)
            result_df.to_csv(SIM_NAME+"/simulation_state.csv", index=False)
            
            # save oracle data for rust/ts reprod 
            max_t = int(max(oracle.timestamps))
            all_timestamps = list(range(max_t))
            all_prices = [int(oracle.get_price(t) * 1e10) for t in all_timestamps]
            oracle_df = pd.DataFrame({'timestamp': all_timestamps, 'price': all_prices})
            oracle_df.to_csv(SIM_NAME+"/all_oracle_prices.csv", index=False)

        return result_df
    
class SimpleDriftSim(DriftSim):
    def __init__(self, sim_path, clearing_house, agents):
        self.sim_path = sim_path
        self.name = sim_path
        self.ch_name = f"{sim_path}"
        os.makedirs(self.ch_name, exist_ok=True)
        
        self.clearing_house = clearing_house
        self.agents = agents 
        self.oracle = clearing_house.markets[0].amm.oracle
        setup_run_info(sim_path, self.name)
    
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))
