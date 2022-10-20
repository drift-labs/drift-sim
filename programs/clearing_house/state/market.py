import sys 
import copy 
from dataclasses import dataclass

import driftpy
from driftpy.constants.numeric_constants import * 
from driftpy.math.amm import ( 
    calculate_price, 
    calculate_bid_price_amm,
    calculate_ask_price_amm,
)
from driftpy.math.market import (
    calculate_mark_price, 
    calculate_ask_price, 
    calculate_bid_price,
    calculate_peg_multiplier, 
)
from driftpy.math.repeg import calculate_repeg_cost
from driftpy.math.funding import calculate_long_short_funding

from driftpy._types import AMM, Market

from programs.clearing_house.state.oracle import *

@dataclass
class SimulationAMM(AMM):
    oracle: Oracle # override
    strategies: str = ""

    def __init__(self, **args):
        super_args = {}
        for a in args.copy(): 
            if a in AMM.__dataclass_fields__: 
                super_args[a] = args.pop(a)
        for a in AMM.__dataclass_fields__.keys():
            if a not in super_args:
                super_args[a] = 0 # default
                
        super().__init__(**super_args)

        for a in args: 
            setattr(self, a, args[a])

        self.init_amm()

    def init_amm(self):
        now = 0

        assert self.base_asset_reserve == self.quote_asset_reserve
        self.sqrt_k = self.base_asset_reserve

        # oracle
        if self.oracle is None:
            oracle_price = 1
            print('Warning: oracle not set...')
        else:
            oracle_price = self.oracle.get_price(now)

        self.last_oracle_price = oracle_price
        self.last_oracle_normalised_price = oracle_price
        self.last_oracle_price_twap = oracle_price
        self.last_oracle_price_twap_ts = now 
        
        # market price 
        mark_price = calculate_price(
            self.base_asset_reserve, 
            self.quote_asset_reserve, 
            self.peg_multiplier
        )
        
        self.bid_price_before = calculate_bid_price_amm(self, oracle_price)
        self.ask_price_before = calculate_ask_price_amm(self, oracle_price)
        self.last_ask_price_twap = mark_price
        self.last_bid_price_twap = mark_price
        self.last_mark_price_twap = mark_price
        self.last_mark_price_twap_ts = now 

        # reserves
        self.terminal_quote_asset_reserve = self.quote_asset_reserve
        self.bid_base_asset_reserve = self.base_asset_reserve
        self.bid_quote_asset_reserve = self.quote_asset_reserve
        self.ask_base_asset_reserve = self.base_asset_reserve
        self.ask_quote_asset_reserve = self.quote_asset_reserve
        
        self.total_lp_shares = self.sqrt_k
        self.amm_lp_shares = self.total_lp_shares # amm has it all at once
        
        self.cumulative_funding_rate_long = 0 
        self.cumulative_funding_rate_short = 0 
        self.last_funding_rate_ts = now
        self.mark_std = 0

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
        market_dict.pop("pubkey")
        market_dict.pop("pnl_pool")
        
        amm_dict = copy.deepcopy(self.amm.__dict__)
        amm_dict.pop("oracle")
        b1 = amm_dict['base_asset_reserve']
        q1 = amm_dict['quote_asset_reserve']
        amm_dict['base_asset_reserve'] = f'{b1:.0f}'
        amm_dict['quote_asset_reserve'] = f'{q1:.0f}'

        self.base_asset_amount = self.amm.base_asset_amount_with_amm
        mark_price = calculate_mark_price(self, oracle_price)
        bid_price = calculate_bid_price(self, oracle_price)
        ask_price = calculate_ask_price(self, oracle_price)
        peg = calculate_peg_multiplier(self.amm, oracle_price)
        wouldbe_peg_cost = calculate_repeg_cost(self.amm, peg)
        
        long_funding, short_funding = calculate_long_short_funding(self)
        predicted_long_funding = long_funding
        predicted_short_funding = short_funding
        last_mid_price_twap = (amm_dict['last_bid_price_twap']+amm_dict['last_ask_price_twap'])/2
        repeg_to_oracle_cost = calculate_repeg_cost(self.amm, int(oracle_price * 1e3))
                    
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
            if key in data:
                data[key] /= 1e6
        
        return data 
