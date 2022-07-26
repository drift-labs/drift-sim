import sys 
import driftpy
import copy 

from dataclasses import dataclass, field

from driftpy.constants.numeric_constants import * 
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.amm import ( 
    calculate_price, 
    calculate_bid_price_amm,
    calculate_ask_price_amm,
)

from programs.clearing_house.state.oracle import *

from solana.publickey import PublicKey

import json 
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt 

from driftpy.types import AMM, Market

@dataclass
class SimulationAMM(AMM):
    oracle: Oracle # override
    strategies: str = ""
    upnl: int = 0

    lp_funding_payment: int = 0
    cumulative_net_quote_asset_amount_per_lp: int = 0

    def __init__(self, **args):
        super_args = {}
        for a in args.copy(): 
            if a in AMM.__dataclass_fields__: 
                super_args[a] = args.pop(a)
        super().__init__(**super_args)

        for a in args: 
            setattr(self, a, args[a])

        init_amm(self)

@dataclass
class SimulationMarket(Market): 
    amm: SimulationAMM

    def __init__(self, **args):
        super_args = {}
        for a in args.copy(): 
            if a in Market.__dataclass_fields__: 
                super_args[a] = args.pop(a)
        super().__init__(**super_args)

        for a in args: 
            setattr(self, a, args[a])

    def to_json(self, now):
        # current prices 
        mark_price = calculate_mark_price(self)
        oracle_price = self.amm.oracle.get_price(now)
        
        market_dict = copy.deepcopy(self.__dict__)
        market_dict.pop("amm")
        
        amm_dict = copy.deepcopy(self.amm.__dict__)
        amm_dict.pop("oracle")
        b1 = amm_dict['base_asset_reserve']
        q1 = amm_dict['quote_asset_reserve']
        amm_dict['base_asset_reserve'] = f'{b1:.0f}'
        amm_dict['quote_asset_reserve'] = f'{q1:.0f}'

        mark_price = calculate_mark_price(self, oracle_price)
        bid_price = calculate_bid_price(self, oracle_price)
        ask_price = calculate_ask_price(self, oracle_price)
        peg = calculate_peg_multiplier(self.amm, oracle_price)
        wouldbe_peg_cost = calculate_repeg_cost(self, peg)[0]
        
        long_funding, short_funding = calculate_long_short_funding(self)
        predicted_long_funding = long_funding
        predicted_short_funding = short_funding
        last_mid_price_twap = (amm_dict['last_bid_price_twap']+amm_dict['last_ask_price_twap'])/2
        repeg_to_oracle_cost = calculate_repeg_cost(self, int(oracle_price * 1e3))[0]
                    
        # all in one 
        data = dict(
            mark_price=mark_price, 
            oracle_price=oracle_price,
            bid_price=bid_price, 
            ask_price=ask_price, 
            wouldbe_peg=peg/1e3, 
            wouldbe_peg_cost=wouldbe_peg_cost, 
            predicted_long_funding=predicted_long_funding,
            predicted_short_funding=predicted_short_funding,
            last_mid_price_twap=last_mid_price_twap,
            repeg_to_oracle_cost=repeg_to_oracle_cost
        ) | market_dict | amm_dict
        
        # rescale 
        for key in ['total_fee', 'total_mm_fees', 'total_exchange_fees', 'total_fee_minus_distributions']:
            data[key] /= 1e6
        
        return data 
       
def init_amm(amm: SimulationAMM):
    now = 0
    
    oracle_price = amm.oracle.get_price(now)
    amm.last_oracle_price = oracle_price
    amm.last_oracle_normalised_price = oracle_price

    amm.last_oracle_price_twap = oracle_price
    amm.last_oracle_price_twap_ts = now 
    
    mark_price = calculate_price(
        amm.base_asset_reserve, 
        amm.quote_asset_reserve, 
        amm.peg_multiplier
    )
    
    if amm.base_asset_reserve != amm.quote_asset_reserve:
        amm.sqrt_k = int((
            amm.base_asset_reserve/1e13 * amm.quote_asset_reserve/1e13
        ) ** .5) * 1e13
    else:
        amm.sqrt_k = amm.base_asset_reserve
    
    amm.total_lp_shares = amm.sqrt_k
    amm.amm_lp_shares = amm.total_lp_shares # amm has it all at once
    
    amm.bid_price_before = calculate_bid_price_amm(amm, oracle_price)
    amm.ask_price_before = calculate_ask_price_amm(amm, oracle_price)
    amm.last_ask_price_twap = mark_price
    amm.last_bid_price_twap = mark_price
    amm.last_mark_price_twap = mark_price
    amm.last_mark_price_twap_ts = now 
    
    amm.cumulative_funding_rate_long = 0 
    amm.cumulative_funding_rate_short = 0 
    amm.last_funding_rate_ts = now
    amm.mark_std = 0
    amm.terminal_quote_asset_reserve = amm.quote_asset_reserve

# @dataclass
# class Market: 
#     amm: AMM 
#     market_index: int = 0
    
#     # TODO: fix typing/name scheme here to match types.py
#     base_asset_amount_long: int = 0
#     base_asset_amount_short: int = 0 

#     base_asset_amount: int = 0
#     total_base_asset_amount: int = 0

#     open_interest: int = 0
#     total_exchange_fees: int = 0 
#     total_mm_fees: int = 0 

#     margin_ratio_initial: int = 1000
#     margin_ratio_maintenance: int = 625 
#     margin_ratio_partial: int = 500
    
    # def to_json(self, now):
    #     # current prices 
    #     mark_price = calculate_mark_price(self)
    #     oracle_price = self.amm.oracle.get_price(now)
        
    #     market_dict = copy.deepcopy(self.__dict__)
    #     market_dict.pop("amm")
        
    #     amm_dict = copy.deepcopy(self.amm.__dict__)
    #     amm_dict.pop("oracle")
    #     b1 = amm_dict['base_asset_reserve']
    #     q1 = amm_dict['quote_asset_reserve']
    #     amm_dict['base_asset_reserve'] = f'{b1:.0f}'
    #     amm_dict['quote_asset_reserve'] = f'{q1:.0f}'

    #     mark_price = calculate_mark_price(self, oracle_price)
    #     bid_price = calculate_bid_price(self, oracle_price)
    #     ask_price = calculate_ask_price(self, oracle_price)
    #     peg = calculate_peg_multiplier(self.amm, oracle_price)
    #     wouldbe_peg_cost = calculate_repeg_cost(self, peg)[0]
        
    #     long_funding, short_funding = calculate_long_short_funding(self)
    #     predicted_long_funding = long_funding
    #     predicted_short_funding = short_funding
    #     last_mid_price_twap = (amm_dict['last_bid_price_twap']+amm_dict['last_ask_price_twap'])/2
    #     repeg_to_oracle_cost = calculate_repeg_cost(self, int(oracle_price * 1e3))[0]
                    
    #     # all in one 
    #     data = dict(
    #         mark_price=mark_price, 
    #         oracle_price=oracle_price,
    #         bid_price=bid_price, 
    #         ask_price=ask_price, 
    #         wouldbe_peg=peg/1e3, 
    #         wouldbe_peg_cost=wouldbe_peg_cost, 
    #         predicted_long_funding=predicted_long_funding,
    #         predicted_short_funding=predicted_short_funding,
    #         last_mid_price_twap=last_mid_price_twap,
    #         repeg_to_oracle_cost=repeg_to_oracle_cost
    #     ) | market_dict | amm_dict
        
    #     # rescale 
    #     for key in ['total_fee', 'total_mm_fees', 'total_exchange_fees', 'total_fee_minus_distributions']:
    #         data[key] /= 1e6
        
    #     return data 
       
